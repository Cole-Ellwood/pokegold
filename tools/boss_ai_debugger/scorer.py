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

    if kind == "switch":
        if "ace_preservation" in tags or "switching" in tags or "hidden_coverage" in tags:
            _add(contributions, "public_switch", 8, "switch addresses a public risk in this fixture")
        if "preserve" in text or "handles" in text:
            _add(contributions, "preserve_value", 4, "action text preserves a high-value mon")
        if "same fire pressure" in text or "still risks" in text or "likely still bad" in text:
            _add(contributions, "bad_pivot", -8, "switch target does not solve the visible threat")

    if kind == "move":
        damage_like = _is_damage_like_move(name)
        if damage_like and ("immediate" in text or "direct" in text or "clean" in text):
            _add(contributions, "tempo_damage", 5, "move takes tempo instead of waiting")
        if name in COVERAGE_NAMES or (damage_like and ("coverage" in text or "punish" in text)):
            _add(contributions, "coverage", 7, "move uses public coverage or visible punish")
        if damage_like and _has_any(text, WEAK_DAMAGE_TEXT):
            _add(contributions, "weak_chip", -4, "text marks this damage as low-impact chip")
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
            if _has_any(text, SETUP_RISK_TEXT):
                _add(contributions, "setup_risk", -10, "public pressure makes setup risky")
        if name in DEBUFF_NAMES:
            _add(contributions, "debuff_control", 3, "one debuff can reduce public counterplay risk")
        if name in STATUS_NAMES:
            _add(contributions, "status_identity", 5, "status/control move matches boss identity")
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
        if name in PHAZING_NAMES:
            _add(contributions, "denial", 6, "phazing denies public setup or switch patterns")

    if "hidden_coverage" in tags:
        if kind == "switch":
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
