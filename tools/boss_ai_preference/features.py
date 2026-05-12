from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .damage_estimates import attach_damage_estimates
from .data import DEFAULT_FIXTURES_PATH, PreferenceDataError, load_fixtures
from .threat_availability import attach_incoming_threats


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FEATURE_REPORT_PATH = ROOT / "audit" / "boss_ai_preference" / "feature_report.md"
DEFAULT_FEATURE_JSON_PATH = ROOT / "audit" / "boss_ai_preference" / "feature_report.json"

SETUP_MOVES = {
    "agility",
    "curse",
    "dragon dance",
    "double team",
    "growth",
    "swords dance",
}
STATUS_MOVES = {
    "confuse ray",
    "encore",
    "hypnosis",
    "sleep powder",
    "stun spore",
    "thunder wave",
    "toxic",
}
SLEEP_MOVES = {"hypnosis", "sleep powder", "spore", "lovely kiss"}
SPEED_CONTROL_MOVES = {"agility", "stun spore", "thunder wave"}
SACRIFICE_MOVES = {"destiny bond", "explosion", "selfdestruct"}
PRIORITY_MOVES = {"extremespeed", "quick attack"}
LOCK_MOVES = {"outrage", "rollout"}
RECOVERY_MOVES = {"milk drink", "recover", "rest", "synthesis"}
PHAZING_MOVES = {"roar", "whirlwind"}
PROBE_WORDS = {"probe", "scout", "reveal", "reveals", "information"}
GREED_WORDS = {"greedy", "setup", "set up", "boost", "snowball"}
PUNISH_WORDS = {"punish", "kills", "ko", "ohko", "threat", "pressure"}
RISK_WORDS = {"risk", "risky", "dies", "die", "bad", "punish", "weak"}


def enrich_fixtures(fixtures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach public review metadata used by V2 feature extraction."""
    return attach_incoming_threats(attach_damage_estimates(fixtures))


def action_text(action: dict[str, Any]) -> str:
    return " ".join(
        str(action.get(key, ""))
        for key in ("id", "kind", "name", "explanation", "public_tradeoff")
    ).lower()


def action_name(action: dict[str, Any]) -> str:
    return str(action.get("name", "")).strip().lower()


def add(features: dict[str, float], name: str, value: float = 1.0) -> None:
    if value:
        features[name] = round(float(value), 4)


def parse_hp_percent(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return max(0.0, min(100.0, float(value)))
    if not isinstance(value, str):
        return None
    match = re.search(r"(\d+(?:\.\d+)?)\s*%", value)
    if not match:
        return None
    return max(0.0, min(100.0, float(match.group(1))))


def bucket(value: float, thresholds: tuple[tuple[float, str], ...]) -> str:
    for threshold, label in thresholds:
        if value <= threshold:
            return label
    return thresholds[-1][1]


def fixture_hp_features(fixture: dict[str, Any], features: dict[str, float]) -> None:
    state = fixture.get("state", {})
    boss_hp = parse_hp_percent(
        state.get("boss", {}).get("active", {}).get("hp")
    )
    player_hp = parse_hp_percent(
        state.get("player", {}).get("active", {}).get("hp")
    )
    if boss_hp is not None:
        add(features, f"boss_hp_{bucket(boss_hp, ((25, 'critical'), (50, 'low'), (75, 'mid'), (100, 'high')))}")
        add(features, "boss_hp_percent", boss_hp / 100)
    if player_hp is not None:
        add(features, f"player_hp_{bucket(player_hp, ((25, 'critical'), (50, 'low'), (75, 'mid'), (100, 'high')))}")
        add(features, "player_hp_percent", player_hp / 100)
    if boss_hp is not None and player_hp is not None:
        add(features, "boss_hp_minus_player_hp", (boss_hp - player_hp) / 100)


def damage_features(action: dict[str, Any], features: dict[str, float]) -> None:
    estimate = action.get("damage_estimate")
    if not isinstance(estimate, dict):
        return
    low = estimate.get("low_percent")
    high = estimate.get("high_percent")
    if not isinstance(low, (int, float)) or not isinstance(high, (int, float)):
        return
    average = (float(low) + float(high)) / 2
    add(features, "damage_low_percent", float(low) / 100)
    add(features, "damage_high_percent", float(high) / 100)
    add(features, "damage_average_percent", average / 100)
    add(features, f"damage_bucket_{bucket(average, ((10, 'chip'), (35, 'meaningful'), (65, 'major'), (99, 'near_ko'), (999, 'ko')))}")
    if high >= 100:
        add(features, "ko_possible")
    if low >= 100:
        add(features, "ko_confirmed")
    if average >= 50:
        add(features, "two_hko_or_better")


def public_threat_features(fixture: dict[str, Any], features: dict[str, float]) -> list[str]:
    threats = fixture.get("incoming_threats", [])
    if not isinstance(threats, list):
        return []

    active = [
        threat
        for threat in threats
        if isinstance(threat, dict) and threat.get("immediacy") == "active"
    ]
    switch = [
        threat
        for threat in threats
        if isinstance(threat, dict) and threat.get("immediacy") == "switch"
    ]
    major_or_lethal = [
        threat
        for threat in active
        if threat.get("severity") in {"major", "lethal"}
    ]
    if active:
        add(features, "public_active_threat_count", len(active))
    if switch:
        add(features, "public_switch_threat_count", len(switch))
    if major_or_lethal:
        add(features, "public_major_or_lethal_active_threat")

    likely = [
        threat
        for threat in active
        if isinstance(threat.get("likelihood"), int) and threat["likelihood"] >= 75
    ]
    if likely:
        add(features, "public_likely_active_threat")

    sources = sorted(
        {
            str(source)
            for threat in threats
            if isinstance(threat, dict)
            for source in threat.get("sources", [])
        }
    )
    return sources


def action_class_features(action: dict[str, Any], features: dict[str, float]) -> None:
    kind = str(action.get("kind", "unknown"))
    name = action_name(action)
    text = action_text(action)
    add(features, f"kind_{kind}")

    for tag, names in (
        ("setup", SETUP_MOVES),
        ("status", STATUS_MOVES),
        ("sleep", SLEEP_MOVES),
        ("speed_control", SPEED_CONTROL_MOVES),
        ("sacrifice", SACRIFICE_MOVES),
        ("priority", PRIORITY_MOVES),
        ("lock", LOCK_MOVES),
        ("recovery", RECOVERY_MOVES),
        ("phazing", PHAZING_MOVES),
    ):
        if name in names:
            add(features, f"move_class_{tag}")

    if any(word in text for word in PROBE_WORDS):
        add(features, "text_information_probe")
    if any(word in text for word in GREED_WORDS):
        add(features, "text_setup_or_greedy")
    if any(word in text for word in PUNISH_WORDS):
        add(features, "text_tempo_or_punish")
    if any(word in text for word in RISK_WORDS):
        add(features, "text_visible_risk")
    if "preserve" in text or "save" in text:
        add(features, "text_preserve_value")
    if "iconic" in text or "leader-flavored" in text or "flavored" in text:
        add(features, "text_personality_style")


def fixture_tag_features(fixture: dict[str, Any], features: dict[str, float]) -> None:
    for tag in fixture.get("tags", []):
        if isinstance(tag, str) and tag:
            add(features, f"fixture_tag_{tag}")


def extract_action_features(
    fixture: dict[str, Any],
    action: dict[str, Any],
) -> dict[str, Any]:
    features: dict[str, float] = {}
    fixture_tag_features(fixture, features)
    fixture_hp_features(fixture, features)
    action_class_features(action, features)
    damage_features(action, features)
    threat_sources = public_threat_features(fixture, features)

    return {
        "fixture_id": fixture["id"],
        "leader": fixture["leader"],
        "action_id": action["id"],
        "action_name": action["name"],
        "features": dict(sorted(features.items())),
        "feature_sources": {
            "incoming_threats": threat_sources,
            "damage_estimate": ["tools.boss_ai_preference.damage_estimates"]
            if action.get("damage_estimate")
            else [],
        },
    }


def extract_fixture_features(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    return [extract_action_features(fixture, action) for action in fixture.get("actions", [])]


def extract_plan_features(
    fixture: dict[str, Any],
    plan: dict[str, Any],
) -> dict[str, Any]:
    features: dict[str, float] = {}
    add(features, "kind_plan")
    add(features, f"plan_shape_{plan.get('shape', 'unknown')}")
    add(features, f"plan_phase_{plan.get('phase', 'unknown')}")
    horizon = plan.get("horizon", 1)
    if isinstance(horizon, (int, float)) and not isinstance(horizon, bool):
        add(features, "plan_horizon", min(5.0, max(1.0, float(horizon))) / 5.0)

    for condition in plan.get("stop_conditions", []):
        if isinstance(condition, str) and condition:
            add(features, f"stop_{condition}")
    for condition in plan.get("initiation_conditions", []):
        if isinstance(condition, str) and condition:
            add(features, f"init_{condition}")
    for rule in plan.get("branch_rules", []):
        if not isinstance(rule, dict):
            continue
        if_condition = rule.get("if")
        then = rule.get("then")
        if isinstance(if_condition, str) and if_condition:
            add(features, f"branch_if_{if_condition}")
        if isinstance(then, str) and then:
            add(features, f"branch_then_{then}")

    actions_by_id = {
        action["id"]: action
        for action in fixture.get("actions", [])
        if isinstance(action, dict) and action.get("id")
    }
    seen_action_ids: set[str] = set()
    for step in plan.get("steps", []):
        if not isinstance(step, dict):
            continue
        step_action_id = step.get("action_id")
        if not isinstance(step_action_id, str) or step_action_id in seen_action_ids:
            continue
        seen_action_ids.add(step_action_id)
        action = actions_by_id.get(step_action_id)
        if action is None:
            continue
        action_features: dict[str, float] = {}
        action_class_features(action, action_features)
        damage_features(action, action_features)
        for name, value in action_features.items():
            add(features, f"plan_action_{name}", value)

    return {
        "fixture_id": fixture["id"],
        "leader": fixture["leader"],
        "plan_id": plan["id"],
        "plan_label": plan["label"],
        "features": dict(sorted(features.items())),
        "feature_sources": {
            "plan": ["tools.boss_ai_preference.plans"],
            "rollout": [str(plan.get("rollout_mode", "unknown"))],
        },
    }


def build_feature_report(fixtures: list[dict[str, Any]]) -> dict[str, Any]:
    enriched = enrich_fixtures(fixtures)
    action_rows = [
        action_row
        for fixture in enriched
        for action_row in extract_fixture_features(fixture)
    ]
    feature_support: Counter[str] = Counter()
    leader_counts: Counter[str] = Counter()
    feature_by_leader: dict[str, Counter[str]] = defaultdict(Counter)
    for row in action_rows:
        leader = row["leader"]
        leader_counts[leader] += 1
        for name, value in row["features"].items():
            if value:
                feature_support[name] += 1
                feature_by_leader[leader][name] += 1

    return {
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "fixture_count": len(fixtures),
        "action_count": len(action_rows),
        "feature_count": len(feature_support),
        "feature_support": dict(sorted(feature_support.items())),
        "leader_action_counts": dict(sorted(leader_counts.items())),
        "leader_top_features": {
            leader: dict(counter.most_common(8))
            for leader, counter in sorted(feature_by_leader.items())
        },
        "actions": action_rows,
    }


def render_feature_report(report: dict[str, Any]) -> str:
    lines = [
        "# Boss AI Preference Feature Report",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Fixtures: {report['fixture_count']}",
        f"- Actions: {report['action_count']}",
        f"- Non-zero feature names: {report['feature_count']}",
        "",
        "## Highest Support Features",
        "",
    ]
    for name, count in Counter(report["feature_support"]).most_common(20):
        lines.append(f"- `{name}`: {count}")
    lines.extend(["", "## Leader Coverage", ""])
    for leader, count in report["leader_action_counts"].items():
        top = ", ".join(
            f"`{name}`={value}"
            for name, value in report["leader_top_features"].get(leader, {}).items()
        )
        lines.append(f"- {leader}: {count} action(s); {top}")
    lines.append("")
    return "\n".join(lines)


def write_feature_report(
    *,
    fixtures_path: Path = DEFAULT_FIXTURES_PATH,
    out_path: Path = DEFAULT_FEATURE_REPORT_PATH,
    json_out_path: Path | None = DEFAULT_FEATURE_JSON_PATH,
) -> dict[str, Any]:
    fixtures = load_fixtures(fixtures_path)
    report = build_feature_report(fixtures)
    markdown = render_feature_report(report)

    if str(out_path) == "-":
        print(markdown)
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(markdown, encoding="utf-8", newline="\n")

    if json_out_path is not None:
        json_out_path.parent.mkdir(parents=True, exist_ok=True)
        json_out_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return report


def feature_vector_for_action(
    fixtures: list[dict[str, Any]],
    fixture_id: str,
    action_id: str,
) -> dict[str, float]:
    for fixture in enrich_fixtures(fixtures):
        if fixture["id"] != fixture_id:
            continue
        for row in extract_fixture_features(fixture):
            if row["action_id"] == action_id:
                return dict(row["features"])
        raise PreferenceDataError(
            f"fixture {fixture_id!r}: action_id {action_id!r} is not in fixture"
        )
    raise PreferenceDataError(f"unknown fixture_id {fixture_id!r}")
