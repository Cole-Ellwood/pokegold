from __future__ import annotations

from typing import Any


DEFAULT_ROLLOUT_MODE = "deterministic_public_worst_case"
ALLOWED_ROLLOUT_MODES = (
    "deterministic_public_worst_case",
    "public_belief_samples",
    "human_trace_replay",
)
ROLLOUT_MODE_ALIASES = {
    "deterministic-public-worst-case": "deterministic_public_worst_case",
    "public-belief-samples": "public_belief_samples",
    "human-trace-replay": "human_trace_replay",
}

SEVERITY_RANK = {
    "lethal": 4,
    "major": 3,
    "meaningful": 2,
    "chip": 1,
}


def normalize_rollout_mode(value: str | None) -> str:
    if value is None or value == "":
        return DEFAULT_ROLLOUT_MODE
    normalized = ROLLOUT_MODE_ALIASES.get(value, value)
    if normalized not in ALLOWED_ROLLOUT_MODES:
        allowed = ", ".join(ALLOWED_ROLLOUT_MODES)
        raise ValueError(f"rollout mode must be one of {allowed}")
    return normalized


def active_player_state(fixture: dict[str, Any]) -> dict[str, Any]:
    state = fixture.get("state", {})
    player = state.get("player", {})
    active = player.get("active", {})
    return active if isinstance(active, dict) else {}


def active_boss_state(fixture: dict[str, Any]) -> dict[str, Any]:
    state = fixture.get("state", {})
    boss = state.get("boss", {})
    active = boss.get("active", {})
    return active if isinstance(active, dict) else {}


def revealed_player_moves(fixture: dict[str, Any]) -> list[str]:
    moves = active_player_state(fixture).get("revealed_moves", [])
    if not isinstance(moves, list):
        return []
    return sorted({str(move) for move in moves if str(move).strip()})


def incoming_public_threats(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    threats = fixture.get("incoming_threats", [])
    if not isinstance(threats, list):
        return []
    return [threat for threat in threats if isinstance(threat, dict)]


def public_player_move_buckets(fixture: dict[str, Any]) -> dict[str, list[str] | int]:
    revealed = revealed_player_moves(fixture)
    revealed_lower = {move.lower() for move in revealed}
    plausible: set[str] = set()
    impossible: set[str] = set()

    for threat in incoming_public_threats(fixture):
        move = str(threat.get("move") or threat.get("move_id") or "").strip()
        if not move:
            continue
        if move.lower() in revealed_lower:
            continue
        likelihood = threat.get("likelihood")
        if isinstance(likelihood, int) and likelihood <= 0:
            impossible.add(move)
        elif threat.get("bucket") != "0%":
            plausible.add(move)

    unknown_slots = max(0, 4 - len(revealed))
    if unknown_slots == 0:
        plausible.clear()

    return {
        "revealed": revealed,
        "plausible": sorted(plausible),
        "impossible": sorted(impossible),
        "unknown_slots": unknown_slots,
    }


def strongest_public_punish(fixture: dict[str, Any]) -> dict[str, Any] | None:
    candidates = [
        threat
        for threat in incoming_public_threats(fixture)
        if threat.get("immediacy") == "active"
        and isinstance(threat.get("likelihood"), int)
        and int(threat["likelihood"]) > 0
    ]
    if not candidates:
        return None

    def sort_key(threat: dict[str, Any]) -> tuple[int, int, float, str]:
        damage = threat.get("damage") if isinstance(threat.get("damage"), dict) else {}
        high = damage.get("high_percent", 0)
        high_value = float(high) if isinstance(high, (int, float)) else 0.0
        return (
            SEVERITY_RANK.get(str(threat.get("severity")), 0),
            int(threat.get("likelihood", 0)),
            high_value,
            str(threat.get("move", "")),
        )

    return sorted(candidates, key=sort_key, reverse=True)[0]


def public_belief_summary(fixture: dict[str, Any]) -> dict[str, Any]:
    state = fixture.get("state", {})
    boss = state.get("boss", {}) if isinstance(state.get("boss"), dict) else {}
    player = state.get("player", {}) if isinstance(state.get("player"), dict) else {}
    return {
        "boss_private": {
            "active": boss.get("active", {}),
            "bench": boss.get("bench", []),
            "legal_actions": [
                {
                    "id": action.get("id"),
                    "name": action.get("name"),
                    "kind": action.get("kind"),
                }
                for action in fixture.get("actions", [])
                if isinstance(action, dict)
            ],
        },
        "player_public": {
            "active": player.get("active", {}),
            "seen_party": player.get("seen_party", []),
            "move_buckets": public_player_move_buckets(fixture),
        },
        "field": state.get("field", {}),
        "public_notes": state.get("public_notes", []),
    }


def public_response_text(fixture: dict[str, Any], mode: str) -> str:
    threat = strongest_public_punish(fixture)
    if threat is None:
        return "No strong active public punish is surfaced; player response remains unknown."

    move = str(threat.get("move") or threat.get("move_id"))
    bucket = str(threat.get("bucket", "public"))
    severity = str(threat.get("severity", "unknown"))
    if mode == "public_belief_samples":
        return f"Sampled public belief may include {move} ({bucket}, {severity})."
    if mode == "human_trace_replay":
        return f"Replay mode keeps the captured public response context; strongest surfaced punish is {move}."
    return f"Assume the player may choose the strongest public punish: {move} ({bucket}, {severity})."


def expanded_plan_steps(plan: dict[str, Any]) -> list[dict[str, Any]]:
    raw_steps = plan.get("steps", [])
    if not isinstance(raw_steps, list):
        raw_steps = []
    explicit_steps = [
        dict(step)
        for step in raw_steps
        if isinstance(step, dict) and isinstance(step.get("turn"), int)
    ]
    steps_by_turn = {int(step["turn"]): step for step in explicit_steps}
    try:
        horizon = max(1, min(5, int(plan.get("horizon", 3))))
    except (TypeError, ValueError):
        horizon = 3

    expanded: list[dict[str, Any]] = []
    previous: dict[str, Any] | None = None
    for turn in range(1, horizon + 1):
        explicit = steps_by_turn.get(turn)
        if explicit is not None:
            step = dict(explicit)
            step["projected"] = False
            expanded.append(step)
            previous = step
            continue

        if previous is None:
            step = {
                "turn": turn,
                "label": "Re-score position",
                "projected": True,
                "projection_note": "No earlier boss action is fixed for this line.",
            }
        elif previous.get("repeat_until"):
            step = dict(previous)
            step["turn"] = turn
            step["projected"] = True
            step["projection_note"] = "Continue while its repeat/stop rule remains true."
        else:
            step = {
                "turn": turn,
                "label": "Re-score position",
                "actor": previous.get("actor", "boss"),
                "projected": True,
                "projection_note": "No forced action; re-evaluate from the new public state.",
            }
        expanded.append(step)
    return expanded


def project_plan(
    fixture: dict[str, Any],
    plan: dict[str, Any],
    *,
    rollout_mode: str = DEFAULT_ROLLOUT_MODE,
) -> dict[str, Any]:
    mode = normalize_rollout_mode(rollout_mode)
    steps = expanded_plan_steps(plan)
    projection: list[dict[str, Any]] = []
    for step in steps:
        projection.append(
            {
                "turn": step.get("turn"),
                "boss_action_id": step.get("action_id"),
                "boss_action": step.get("label", step.get("action_id")),
                "actor": step.get("actor", "boss"),
                "projected": bool(step.get("projected")),
                "projection_note": step.get("projection_note", ""),
                "player_public_response": public_response_text(fixture, mode),
                "stop_checks": list(plan.get("stop_conditions", [])),
            }
        )

    buckets = public_player_move_buckets(fixture)
    assumptions = [
        "Boss-side actions use the fixture's legal boss action list.",
        "Player-side moves are separated into revealed, plausible, impossible, and unknown.",
        "No unrevealed player move is treated as fact.",
    ]
    if buckets["unknown_slots"]:
        assumptions.append(f"{buckets['unknown_slots']} player moveslot(s) remain unknown.")
    if mode == "public_belief_samples":
        assumptions.append("Sample rows are coarse public-belief prompts, not exact simulator lines.")
    elif mode == "human_trace_replay":
        assumptions.append("Trace replay mode is only as complete as the captured public trace.")
    else:
        assumptions.append("Worst-case mode assumes the strongest currently surfaced public punish.")

    return {
        "rollout_mode": mode,
        "projection": projection,
        "assumptions": assumptions,
        "player_move_buckets": buckets,
    }
