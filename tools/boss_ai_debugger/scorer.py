from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


SETUP_NAMES = {
    "agility",
    "curse",
    "dragon dance",
    "double team",
    "growth",
    "quiver dance",
    "swords dance",
}
DEBUFF_NAMES = {
    "flash",
    "growl",
    "leer",
    "sand attack",
    "screech",
    "smokescreen",
    "tail whip",
}
STATUS_NAMES = {
    "confuse ray",
    "encore",
    "hypnosis",
    "sleep powder",
    "stun spore",
    "thunder wave",
    "toxic",
}
SLEEP_NAMES = {"hypnosis", "lovely kiss", "sleep powder", "spore"}
SACRIFICE_NAMES = {"destiny bond", "explosion"}
PRIORITY_NAMES = {"extremespeed", "quick attack"}
COVERAGE_NAMES = {
    "crunch",
    "earthquake",
    "ice beam",
    "ice punch",
    "psychic",
    "rock slide",
    "shadow ball",
    "thunder",
    "thunderpunch",
}
LOCK_NAMES = {"outrage", "rollout"}
RECOVERY_NAMES = {"milk drink", "recover", "rest", "synthesis"}
PHAZING_NAMES = {"roar", "whirlwind"}
HAZARD_NAMES = {"spikes"}
NON_DAMAGE_NAMES = (
    SETUP_NAMES
    | STATUS_NAMES
    | DEBUFF_NAMES
    | {"attract", "baton pass", "lock-on", "mean look", "protect", "spikes", "substitute"}
)
SETUP_SAFE_TEXT = {
    "cannot punish",
    "can set up",
    "free setup",
    "safe setup",
    "setup opportunity",
    "survives",
}
SETUP_RISK_TEXT = {
    "direct pressure",
    "greedy",
    "risky",
    "super-effective",
    "throw",
    "under fire pressure",
    "visible pressure",
}
WEAK_DAMAGE_TEXT = {
    "low damage",
    "minimal damage",
    "resisted",
    "resistance",
    "weak chip",
}
PUBLIC_TYPE_FAIL_TEXT = {
    "bad into a public dark",
    "does not affect",
    "fail into dark",
    "failed psychic",
    "no effect",
    "public fail into dark",
}
BAD_PIVOT_TEXT = {
    "same fire pressure",
    "still risks",
    "likely still bad",
    "does not solve",
    "does not cleanly",
    "still weak",
    "stays exposed",
}


TYPE_WALL_PIVOT_TEXT = {
    "hard walls",
    "hard wall",
}


PUBLIC_NOTES_CHIP_QUALIFIER_TEXT = {
    # Labeler patterns that mean "the revealed player threat is chip-grade
    # and does NOT justify giving up a tempo turn on a switch." When the
    # fixture's public_notes explicitly say this, switch actions become
    # bad pivots (over-preserves; "doesn't solve" the real problem because
    # there isn't one). Keep this list narrow — only phrases the labeler
    # uses to mean exactly that, never general "chip" mentions.
    "panic-switch",
    "panic switch",
    "is chip",
    "just chip",
    "pure chip",
    "only chip",
    "reduced chip",
    "not a reason to panic",
}


TYPE_RESIST_PIVOT_TEXT = {
    "fire-resistant",
    "water-resistant",
    "grass-resistant",
    "electric-resistant",
    "ice-resistant",
    "rock-resistant",
    "ground-resistant",
    "flying-resistant",
    "psychic-resistant",
    "fighting-resistant",
    "dark-resistant",
    "ghost-resistant",
    "steel-resistant",
    "bug-resistant",
    "poison-resistant",
    "dragon-resistant",
    "normal-resistant",
}


HAZARD_TEMPO_RISK_TEXT = {
    "cannot afford",
    "fire hit",
    "fire pressure",
    "full hazard turn",
    "lethal pressure",
    "revealed flamethrower",
    "tempo risk",
}


@dataclass(frozen=True)
class Contribution:
    rule: str
    delta: int
    reason: str


def _action_text(action: dict[str, Any]) -> str:
    return " ".join(
        str(action.get(key, ""))
        for key in ("id", "kind", "name", "explanation", "public_tradeoff")
    ).lower()


def _public_text(fixture: dict[str, Any]) -> str:
    state = fixture.get("state", {})
    notes: list[Any] = []
    if isinstance(state, dict):
        public_notes = state.get("public_notes", [])
        if isinstance(public_notes, list):
            notes.extend(public_notes)
    return " ".join(str(note) for note in notes).lower()


def _name(action: dict[str, Any]) -> str:
    return str(action.get("name", "")).lower()


def _is_damage_like_move(name: str) -> bool:
    return name not in NON_DAMAGE_NAMES


def _has_any(text: str, needles: set[str]) -> bool:
    return any(needle in text for needle in needles)


def _hp_percent(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return max(0.0, min(100.0, float(value)))
    if not isinstance(value, str):
        return None
    match = re.search(r"(\d+(?:\.\d+)?)\s*%", value)
    if not match:
        return None
    return max(0.0, min(100.0, float(match.group(1))))


def _player_active_status(fixture: dict[str, Any]) -> str:
    state = fixture.get("state", {})
    if not isinstance(state, dict):
        return ""
    player = state.get("player", {})
    if not isinstance(player, dict):
        return ""
    active = player.get("active", {})
    if not isinstance(active, dict):
        return ""
    return str(active.get("status", "")).strip().lower()


def _player_active_revealed_moves(fixture: dict[str, Any]) -> set[str]:
    state = fixture.get("state", {})
    if not isinstance(state, dict):
        return set()
    player = state.get("player", {})
    if not isinstance(player, dict):
        return set()
    active = player.get("active", {})
    if not isinstance(active, dict):
        return set()
    moves = active.get("revealed_moves", [])
    if not isinstance(moves, list):
        return set()
    return {str(move).strip().lower() for move in moves if str(move).strip()}


def _active_player_revealed_rapid_spin(fixture: dict[str, Any]) -> bool:
    return "rapid spin" in _player_active_revealed_moves(fixture)


def _boss_active(fixture: dict[str, Any]) -> dict[str, Any]:
    state = fixture.get("state", {})
    if not isinstance(state, dict):
        return {}
    boss = state.get("boss", {})
    if not isinstance(boss, dict):
        return {}
    active = boss.get("active", {})
    return active if isinstance(active, dict) else {}


def _boss_active_status(fixture: dict[str, Any]) -> str:
    return str(_boss_active(fixture).get("status", "")).strip().lower()


def _boss_active_hp(fixture: dict[str, Any]) -> float | None:
    return _hp_percent(_boss_active(fixture).get("hp"))


def _has_status(status: str) -> bool:
    return status not in {"", "none"}


def _is_asleep(status: str) -> bool:
    return status in {"sleep", "slp", "asleep"}


def _field_hazards(fixture: dict[str, Any]) -> dict[str, Any]:
    state = fixture.get("state", {})
    if not isinstance(state, dict):
        return {}
    field = state.get("field", {})
    if not isinstance(field, dict):
        return {}
    hazards = field.get("hazards", {})
    return hazards if isinstance(hazards, dict) else {}


def _spikes_layers(fixture: dict[str, Any], side: str) -> int | None:
    hazards = _field_hazards(fixture)
    layers_key = f"{side}_spikes_layers"
    if layers_key in hazards:
        try:
            return max(0, min(3, int(hazards[layers_key])))
        except (TypeError, ValueError):
            return None
    legacy_key = f"{side}_spikes"
    if isinstance(hazards.get(legacy_key), bool):
        return 1 if hazards[legacy_key] else 0
    return None


def _add(
    contributions: list[Contribution],
    rule: str,
    delta: int,
    reason: str,
) -> None:
    if delta:
        contributions.append(Contribution(rule, delta, reason))


def score_action(
    fixture: dict[str, Any],
    action: dict[str, Any],
) -> dict[str, Any]:
    tags = set(fixture.get("tags", []))
    text = _action_text(action)
    name = _name(action)
    kind = str(action.get("kind", ""))
    contributions: list[Contribution] = [Contribution("base", 50, "neutral action floor")]

    if fixture.get("baseline_action_id") == action.get("id"):
        _add(contributions, "baseline", 1, "fixture baseline action for comparison")

    is_bad_pivot = kind == "switch" and _has_any(text, BAD_PIVOT_TEXT)
    public_notes_text = _public_text(fixture)
    chip_qualifier_in_notes = _has_any(public_notes_text, PUBLIC_NOTES_CHIP_QUALIFIER_TEXT)
    if kind == "switch":
        if not is_bad_pivot and (
            "ace_preservation" in tags or "switching" in tags or "hidden_coverage" in tags
        ):
            _add(contributions, "public_switch", 8, "switch addresses a public risk in this fixture")
        if not is_bad_pivot and ("preserve" in text or "handles" in text):
            _add(contributions, "preserve_value", 4, "action text preserves a high-value mon")
        if not is_bad_pivot and _has_any(text, TYPE_WALL_PIVOT_TEXT):
            _add(contributions, "type_wall_pivot", 12, "switch target text marks it as a hard wall to the revealed threat")
        if (
            not is_bad_pivot
            and "hidden_coverage" not in tags
            and _has_any(text, TYPE_RESIST_PIVOT_TEXT)
        ):
            _add(
                contributions,
                "type_resist_pivot",
                6,
                "switch target is type-resistant to a revealed coverage type (not double-counted with hidden_coverage_respect)",
            )
        if is_bad_pivot:
            _add(contributions, "bad_pivot", -8, "switch target does not solve the visible threat")
        if chip_qualifier_in_notes:
            _add(
                contributions,
                "public_notes_chip_qualifier",
                -6,
                "fixture public_notes explicitly qualify the revealed threat as chip / not a reason to panic-switch",
            )

    if kind == "move":
        damage_like = _is_damage_like_move(name)
        if damage_like and ("immediate" in text or "direct" in text or "clean" in text):
            _add(contributions, "tempo_damage", 5, "move takes tempo instead of waiting")
        if name in COVERAGE_NAMES or (damage_like and ("coverage" in text or "punish" in text)):
            _add(contributions, "coverage", 7, "move uses public coverage or visible punish")
        if damage_like and _has_any(text, WEAK_DAMAGE_TEXT):
            _add(contributions, "weak_chip", -4, "text marks this damage as low-impact chip")
        combined_public_text = f"{text} {_public_text(fixture)}"
        if name == "psychic" and "dark" in combined_public_text and _has_any(
            combined_public_text,
            PUBLIC_TYPE_FAIL_TEXT,
        ):
            _add(
                contributions,
                "public_type_immunity_risk",
                -18,
                "public text marks Psychic as failing into a Dark target",
            )
        estimate = action.get("damage_estimate")
        if damage_like and isinstance(estimate, dict):
            low = estimate.get("low_percent")
            high = estimate.get("high_percent")
            target_hp = _hp_percent(estimate.get("target_hp"))
            if (
                isinstance(low, (int, float))
                and isinstance(high, (int, float))
                and target_hp is not None
            ):
                if float(low) >= target_hp:
                    _add(contributions, "ko_confirmed", 12, "damage estimate confirms the target is KOed")
                elif float(high) >= target_hp:
                    _add(contributions, "ko_possible", 8, "damage estimate can KO the target")
        if name in PRIORITY_NAMES:
            _add(contributions, "priority", 6, "priority can answer a low-HP race")
        if name in SETUP_NAMES:
            _add(contributions, "setup_identity", 6, "setup move matches a boss plan")
            if _has_any(text, SETUP_SAFE_TEXT):
                _add(contributions, "setup_window", 12, "public text describes a real setup window")
            if (
                {"sleep", "setup"} <= tags
                and _player_active_status(fixture) in {"sleep", "asleep", "slp"}
            ):
                _add(
                    contributions,
                    "sleeping_target_setup_window",
                    12,
                    "public target sleep creates a setup window that still needs wake-branch review",
                )
            if _has_any(text, SETUP_RISK_TEXT):
                _add(contributions, "setup_risk", -10, "public pressure makes setup risky")
        if name in DEBUFF_NAMES:
            _add(contributions, "debuff_control", 3, "one debuff can reduce public counterplay risk")
        if name in STATUS_NAMES:
            _add(contributions, "status_identity", 5, "status/control move matches boss identity")
            if name in SLEEP_NAMES and {"sleep", "setup"} <= tags and not _has_status(
                _player_active_status(fixture)
            ):
                _add(
                    contributions,
                    "sleep_enables_setup_line",
                    18,
                    "sleep-first line can create the setup turn against an unstatused target",
                )
            if "cheap" in text or "annoying" in text:
                _add(contributions, "taste_risk", -3, "status line needs user taste judgment")
        if name in SACRIFICE_NAMES:
            _add(contributions, "sacrifice_pressure", 4, "sacrifice line can stop a sweep")
            if "stop" in text or "sweep" in text or "trade" in text:
                _add(contributions, "sacrifice_trade_window", 8, "trade line answers a public sweep or clean-switch threat")
            if "cheap" in text:
                _add(contributions, "taste_risk", -2, "sacrifice line may feel cheap")
        if name in LOCK_NAMES:
            _add(contributions, "lock_risk", -8, "locking move is dangerous under public counterplay")
        if name in RECOVERY_NAMES:
            _add(contributions, "preserve_value", 4, "recovery preserves a key boss mon")
            if "spam" in text or "robotic" in text or "automatic" in text:
                _add(contributions, "taste_risk", -4, "recovery can become robotic")
            if name == "rest":
                boss_hp = _boss_active_hp(fixture)
                boss_status = _boss_active_status(fixture)
                if boss_hp == 100:
                    _add(
                        contributions,
                        "full_hp_rest_fails",
                        -16,
                        "local Rest fails at full HP before curing status",
                    )
                elif boss_hp is not None and boss_hp >= 85 and not _has_status(boss_status):
                    _add(
                        contributions,
                        "healthy_rest_no_status",
                        -8,
                        "high-HP Rest without status usually wastes tempo",
                    )
        if name == "sleep talk" and not _is_asleep(_boss_active_status(fixture)):
            _add(contributions, "awake_sleep_talk_fails", -12, "Sleep Talk needs the user to be asleep")
        if name in PHAZING_NAMES:
            _add(contributions, "denial", 6, "phazing denies public setup or switch patterns")
        if name in HAZARD_NAMES:
            player_layers = _spikes_layers(fixture, "player_side")
            _add(contributions, "hazard_identity", 6, "hazard move can change long-game switch economics")
            if player_layers == 0:
                _add(contributions, "first_spikes_layer", 4, "first Spikes layer creates a switching tax")
            elif player_layers == 1:
                _add(contributions, "second_spikes_layer", 7, "second local Spikes layer increases every grounded switch cost")
            elif player_layers == 2:
                _add(contributions, "third_spikes_layer_pressure", 12, "third local Spikes layer pushes grounded switch-ins to quarter-HP damage")
            elif player_layers == 3:
                _add(contributions, "spikes_already_maxed", -20, "local Spikes fails when three layers are already set")
            if player_layers in {1, 2} and _active_player_revealed_rapid_spin(fixture):
                _add(
                    contributions,
                    "active_revealed_spinner_hazard_retention",
                    -18,
                    "active player has publicly revealed Rapid Spin and can erase the stack",
                )
            if _has_any(f"{text} {_public_text(fixture)}", HAZARD_TEMPO_RISK_TEXT):
                _add(contributions, "hazard_tempo_risk", -8, "public pressure makes the hazard turn risky")

    if "hidden_coverage" in tags:
        if kind == "switch":
            if not is_bad_pivot:
                _add(contributions, "hidden_coverage_respect", 10, "public hidden-coverage prior favors preserving the exposed mon")
        elif name in {"outrage", "dragon dance"} or "4x weak" in text or "hidden ice" in text:
            _add(contributions, "hidden_coverage_risk", -10, "action stays exposed to public hidden-coverage risk")

    if "cheapness" in tags and ("cheap" in text or name in SACRIFICE_NAMES):
        _add(contributions, "cheapness_review", -2, "fixture explicitly asks for taste review")

    if "late_game" in tags or "champion" in tags:
        _add(contributions, "late_game_stakes", 2, "late-game leaders should value cleaner decisions")

    total = sum(item.delta for item in contributions)
    total = max(0, min(100, total))
    return {
        "action_id": action["id"],
        "name": action["name"],
        "kind": kind,
        "score": total,
        "contributions": [
            {"rule": item.rule, "delta": item.delta, "reason": item.reason}
            for item in contributions
        ],
    }


def inspect_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    actions = [score_action(fixture, action) for action in fixture["actions"]]
    actions.sort(key=lambda item: (-item["score"], item["action_id"]))
    return {
        "fixture_id": fixture["id"],
        "leader": fixture["leader"],
        "baseline_action_id": fixture.get("baseline_action_id"),
        "tags": fixture.get("tags", []),
        "training_focus": fixture.get("training_focus", ""),
        "actions": actions,
    }


def format_inspection(inspection: dict[str, Any]) -> str:
    lines = [
        f"Fixture: {inspection['fixture_id']} ({inspection['leader']})",
        f"Focus: {inspection['training_focus']}",
        f"Baseline: {inspection.get('baseline_action_id') or 'none'}",
        "",
        "Ranked actions:",
    ]
    for index, action in enumerate(inspection["actions"], start=1):
        lines.append(
            f"{index}. {action['name']} [{action['action_id']}] "
            f"score={action['score']} kind={action['kind']}"
        )
        for contribution in action["contributions"]:
            sign = "+" if contribution["delta"] >= 0 else ""
            lines.append(
                f"   {sign}{contribution['delta']} {contribution['rule']}: "
                f"{contribution['reason']}"
            )
    lines.append("")
    return "\n".join(lines)
