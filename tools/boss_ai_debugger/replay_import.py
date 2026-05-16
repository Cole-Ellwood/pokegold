from __future__ import annotations

import json
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Iterable

from tools.boss_ai_preference.data import PreferenceDataError
from tools.pokemon_mastery.replay_turn_pause import (
    MonState,
    ReplayState,
    SideState,
    clean_mon,
    clean_species,
    read_lines,
    side_from_slot,
    side_known_roster,
    state_before_turn,
    turn_line_indexes,
    turn_segment,
)

from .generators import generate_scenarios, scenario_hash, stamp_scenario, write_jsonl
from .rom_scenarios import evaluate_batch


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPLAY_IMPORT_REPORT = ROOT / "audit" / "boss_ai_debugger" / "replay_import_report.json"
REPLAY_ID_RE = re.compile(r"(?:smogtours-)?gen2ou-\d+")
SIDE_RE = re.compile(r"_(p[12])_")
NON_WORD_RE = re.compile(r"[^a-z0-9]+")
MAX_CANDIDATES = 4

POLICY_KEYWORDS = (
    ("hazard_retention", ("spikes", "rapid spin", "spinblock", "spinner", "subspin")),
    ("cashout", ("explosion", "self-destruct", "self ko", "cash-out", "cashout", "destiny bond")),
    ("resisted_explosion_board_delta", ("resisted explosion", "explosion board delta", "board-delta", "board delta")),
    ("reversible_before_irreversible", ("reversible", "irreversible", "one-shot converter", "one shot converter", "lower-commitment")),
    ("clean_oracle_subset", ("clean-oracle", "clean oracle", "oracle_quality", "oracle quality")),
    ("role_package_ledger", ("role-package", "role package", "package ledger", "public job")),
    ("typed_status_absorber", ("status-tolerant", "typed absorber", "status absorber")),
    ("pass_receiver_survival", ("pass receiver", "receiver survives", "agilitypass", "growthpass", "baton pass receiver")),
    ("sleep_plus_cashout_package", ("sleep plus cash-out", "sleep plus cashout", "lovely kiss", "sleep-cashout")),
    ("route_converter", ("converter", "convert", "route trade", "opens the route")),
    ("branch_action", ("branch", "receiver", "absorber", "counter-handoff", "counter handoff")),
    ("prediction_mix", ("predict", "read", "bluff", "punish", "likely switch")),
    ("setup_timing", ("curse", "growth", "agility", "swords dance", "boost")),
    ("recovery_timing", ("recover", "rest", "resttalk", "wake")),
    ("support_handoff", ("baton pass", "handoff", "support", "phaze", "roar", "whirlwind")),
    ("switch_sack", ("sack", "sacrifice", "preserve", "switch")),
)

FAMILY_KEYWORDS = (
    ("cashout_board_delta", ("resisted explosion", "explosion board delta", "reversible", "irreversible", "sleep plus cash-out", "sleep plus cashout")),
    ("spikes_spin", ("spikes", "rapid spin", "spinblock", "spinner", "subspin")),
    ("switch_sack", ("sack", "sacrifice", "preserve", "explosion", "self-destruct")),
    ("setup_heal", ("curse", "growth", "agility", "recover", "rest", "wake")),
    ("prediction_mix", ("branch", "receiver", "absorber", "predict", "punish", "coverage")),
    ("support_handoff", ("baton pass", "handoff", "support", "phaze", "roar", "whirlwind")),
)

STATUS_MOVES = {
    "hypnosis",
    "lovely kiss",
    "sleep powder",
    "stun spore",
    "thunder wave",
    "toxic",
}
SETUP_MOVES = {"curse", "growth", "agility", "swords dance", "belly drum", "meditate"}
RECOVERY_MOVES = {"recover", "rest", "morning sun", "soft-boiled"}
PHAZE_MOVES = {"roar", "whirlwind"}
SELF_KO_MOVES = {"explosion", "self-destruct", "destiny bond"}
HAZARD_MOVES = {"spikes"}
SPIN_MOVES = {"rapid spin"}
PASS_MOVES = {"baton pass"}
PROTECTION_STATES = {"Substitute", "Protect", "Detect"}
GHOST_SPECIES = {"Gengar", "Misdreavus", "Haunter"}


@dataclass(frozen=True)
class ReplayImportOptions:
    side: str = "all"
    mode: str = "side-known"
    turns: tuple[int, ...] = ()
    limit: int | None = None
    seed: int = 1


def import_replay_sources(
    *,
    logs: Iterable[str | Path] = (),
    mastery_docs: Iterable[Path] = (),
    quick_tests: Path | None = None,
    reviews: Path | None = None,
    options: ReplayImportOptions | None = None,
) -> dict[str, Any]:
    options = options or ReplayImportOptions()
    scenarios: list[dict[str, Any]] = []
    source_reports: list[dict[str, Any]] = []

    for source in logs:
        imported = import_replay_log_source(source, options=options)
        scenarios.extend(imported["scenarios"])
        source_reports.append(imported["report"])
        if reached_limit(scenarios, options.limit):
            scenarios = scenarios[: options.limit]
            break

    if not reached_limit(scenarios, options.limit):
        doc_paths = list(mastery_docs)
        if quick_tests is not None:
            doc_paths.extend(sorted(quick_tests.glob("*.md")))
        if reviews is not None:
            doc_paths.extend(sorted(reviews.glob("*.md")))
        imported_docs = import_mastery_documents(
            doc_paths,
            seed=options.seed,
            limit=None if options.limit is None else max(options.limit - len(scenarios), 0),
        )
        scenarios.extend(imported_docs["scenarios"])
        source_reports.append(imported_docs["report"])

    batch = evaluate_batch(scenarios) if scenarios else empty_batch_report()
    report = {
        "schema_version": 1,
        "scenario_count": len(scenarios),
        "source_count": len(source_reports),
        "side": options.side,
        "mode": options.mode,
        "seed": options.seed,
        "sources": source_reports,
        "batch_summary": {
            "scenario_count": batch["scenario_count"],
            "reviewable_count": batch["reviewable_count"],
            "verdict_counts": batch["verdict_counts"],
            "policy_tag_counts": batch["policy_tag_counts"],
        },
        "public_info_boundary": (
            "replay scenarios use public turn state plus optional advised-side own "
            "move reconstruction; opponent hidden team, moves, PP, held items, and "
            "current input are not imported"
        ),
        "known_limits": [
            "Showdown replay logs are pro-comparison evidence, not local ROM mechanics authority.",
            "Side-known own move reconstruction only includes own moves eventually shown in the log.",
            "Imported scenarios are debugger score-policy probes until ROM materialization confirms a class.",
        ],
    }
    return {"scenarios": scenarios, "report": report}


def import_replay_log_source(
    source: str | Path,
    *,
    options: ReplayImportOptions,
) -> dict[str, Any]:
    path, source_label = materialize_log_source(source)
    lines = read_lines(path)
    turns = selected_turns(lines, options.turns)
    sides = ["p1", "p2"] if options.side == "all" else [options.side]
    scenarios: list[dict[str, Any]] = []
    skipped = 0

    for turn in turns:
        for side in sides:
            scenario = scenario_from_replay_turn(
                lines,
                turn=turn,
                side=side,
                source_label=source_label,
                mode=options.mode,
                seed=options.seed,
            )
            if scenario is None:
                skipped += 1
                continue
            scenarios.append(scenario)
            if reached_limit(scenarios, options.limit):
                break
        if reached_limit(scenarios, options.limit):
            break

    return {
        "scenarios": scenarios,
        "report": {
            "kind": "replay_log",
            "source": source_label,
            "turn_count": len(turns),
            "scenario_count": len(scenarios),
            "skipped_turn_sides": skipped,
        },
    }


def scenario_from_replay_turn(
    lines: list[str],
    *,
    turn: int,
    side: str,
    source_label: str,
    mode: str,
    seed: int,
) -> dict[str, Any] | None:
    actual = actual_action_for_side(lines, turn, side)
    if actual is None:
        return None
    state = state_before_turn(lines, turn)
    boss_side = state.sides[side]
    active = boss_side.active
    if not active or active == "?":
        return None

    roster = side_known_roster(lines, side) if mode == "side-known" else {}
    actions = candidate_actions_for_turn(
        state,
        roster=roster,
        side=side,
        actual=actual,
    )
    if not actions:
        return None

    policy_tags, condition_tags = replay_policy_tags(state, side, actions)
    action_ids = [str(action["id"]) for action in actions]
    actual_id = action_id(actual["kind"], actual["name"])
    expectation = {
        "best_action_ids": [actual_id] if actual_id in action_ids else [],
        "acceptable_action_ids": acceptable_action_ids(actions, actual),
        "policy_tags": sorted(policy_tags | {"replay_oracle"}),
        "condition_tags": sorted(condition_tags | {f"turn_{turn}", f"side_{side}"}),
        "lesson_type": "replay_pro_comparison",
        "confidence": "low" if mode == "spectator-public" else "medium",
        "evidence_refs": [source_label],
        "why": (
            "Imported replay turn: compare current Boss AI scoring against the "
            "actual public replay choice, then review before treating it as policy."
        ),
        "answer_changing_information": [
            "unused own moves absent from side-known reconstruction",
            "private opponent team and move information",
            "local romhack mechanics that differ from vanilla Showdown GSC",
        ],
    }
    scenario = {
        "id": replay_scenario_id(source_label, turn, side, actual["name"], seed),
        "generator": "boss-ai-debugger-replay-import-v1",
        "family": "mastery_replay",
        "seed": seed,
        "tier": "late",
        "state": public_state_for_side(state, side),
        "moves": actions,
        "expectation": expectation,
        "replay_source": {
            "source": source_label,
            "turn": turn,
            "side": side,
            "mode": mode,
            "actual_action": actual,
            "own_side_known_reconstruction": mode == "side-known",
        },
        "notes": [
            f"imported from replay source {source_label}",
            f"turn={turn} side={side} actual={actual['kind']}:{actual['name']}",
        ],
    }
    return stamp_scenario(scenario)


def import_mastery_documents(
    paths: Iterable[Path],
    *,
    seed: int,
    limit: int | None = None,
) -> dict[str, Any]:
    scenarios: list[dict[str, Any]] = []
    scanned = 0
    skipped = 0
    for path in paths:
        if limit is not None and len(scenarios) >= limit:
            break
        if not path.exists() or path.suffix.lower() != ".md":
            skipped += 1
            continue
        scanned += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        scenario = scenario_from_mastery_document(path, text, seed=seed, index=scanned)
        if scenario is None:
            skipped += 1
            continue
        scenarios.append(scenario)
    return {
        "scenarios": scenarios,
        "report": {
            "kind": "mastery_documents",
            "scanned_count": scanned,
            "scenario_count": len(scenarios),
            "skipped_count": skipped,
        },
    }


def scenario_from_mastery_document(
    path: Path,
    text: str,
    *,
    seed: int,
    index: int,
) -> dict[str, Any] | None:
    policy_tags = keyword_tags(text, POLICY_KEYWORDS)
    if not policy_tags:
        return None
    family = family_for_text(text)
    template_seed = stable_seed(f"{seed}:{display_path(path)}")
    template = generate_scenarios(family=family, count=1, seed=template_seed)[0]
    scenario = dict(template)
    relative = display_path(path)
    replay_id = replay_id_for_path_or_text(path, text)
    side = side_for_path(path)
    scenario["id"] = f"mastery_replay_doc_{seed}_{index:05d}_{slug(path.stem)}"
    scenario["generator"] = "boss-ai-debugger-replay-import-v1"
    scenario["family"] = "mastery_replay"
    scenario["mastery_template_family"] = family
    scenario["mastery_source"] = {
        "path": relative,
        "replay_id": replay_id,
        "side": side,
        "kind": "quick_test_or_review",
    }
    scenario["notes"] = [
        f"imported from mastery document {relative}",
        f"template_family={family}",
        *template.get("notes", [])[:2],
    ]
    expectation = dict(scenario.get("expectation", {}))
    expectation["policy_tags"] = sorted(
        set(expectation.get("policy_tags", [])) | policy_tags | {"mastery_replay"}
    )
    expectation["condition_tags"] = sorted(
        set(expectation.get("condition_tags", []))
        | keyword_tags(text, FAMILY_KEYWORDS)
        | {"mastery_doc_seed"}
    )
    refs = list(expectation.get("evidence_refs", []))
    if relative not in refs:
        refs.insert(0, relative)
    expectation["evidence_refs"] = refs
    expectation["lesson_type"] = "mastery_document_projection"
    expectation["confidence"] = str(expectation.get("confidence", "medium"))
    expectation["why"] = (
        "Projected from a scored mastery artifact into an existing debugger "
        "scenario family; review and ROM-materialize before changing policy."
    )
    scenario["expectation"] = expectation
    return restamp_scenario(scenario)


def actual_action_for_side(
    lines: list[str],
    turn: int,
    side: str,
) -> dict[str, str] | None:
    for line in turn_segment(lines, turn):
        parts = line.rstrip("\n").split("|")
        if len(parts) < 4:
            continue
        tag = parts[1]
        if tag == "move" and side_from_slot(parts[2]) == side:
            return {"kind": "move", "name": parts[3]}
        if tag in {"switch", "drag", "replace"} and side_from_slot(parts[2]) == side:
            return {"kind": "switch", "name": clean_mon(parts[2])}
    return None


def candidate_actions_for_turn(
    state: ReplayState,
    *,
    roster: dict[str, MonState],
    side: str,
    actual: dict[str, str],
) -> list[dict[str, Any]]:
    side_state = state.sides[side]
    opponent_side = "p2" if side == "p1" else "p1"
    active = side_state.active
    active_state = side_state.seen.get(active, MonState())
    known_moves = set(active_state.moves)
    if active in roster:
        known_moves.update(roster[active].moves)
    if actual["kind"] == "move":
        known_moves.add(actual["name"])

    ordered_names = sorted(known_moves, key=move_sort_key)[:MAX_CANDIDATES]
    if actual["kind"] == "move" and actual["name"] not in ordered_names:
        ordered_names = (ordered_names[: MAX_CANDIDATES - 1] + [actual["name"]])[:MAX_CANDIDATES]
    actions = [
        action_for_move(name, state=state, side=side, opponent_side=opponent_side)
        for name in ordered_names
    ]

    if actual["kind"] == "switch":
        switch_action = action_for_switch(actual["name"], state=state, side=side)
        actions = [switch_action, *actions[: MAX_CANDIDATES - 1]]

    unique: dict[str, dict[str, Any]] = {}
    for action in actions:
        unique[str(action["id"])] = action
    return list(unique.values())[:MAX_CANDIDATES]


def action_for_move(
    name: str,
    *,
    state: ReplayState,
    side: str,
    opponent_side: str,
) -> dict[str, Any]:
    move_key = name.lower()
    deltas: list[dict[str, Any]] = []
    tags = move_class_tags(name)
    boss_state = state.sides[side]
    opponent_state = state.sides[opponent_side]
    boss_active = boss_state.seen.get(boss_state.active, MonState())
    opponent_active = opponent_state.seen.get(opponent_state.active, MonState())

    if move_key in HAZARD_MOVES:
        if has_spikes(opponent_state):
            add_delta(deltas, "replay.hazard.already_set", 5)
        else:
            add_delta(deltas, "replay.hazard.missing_spikes", -5)
        if public_spinner_live(opponent_state):
            add_delta(deltas, "replay.hazard.public_spin_risk", 6)
    elif move_key in SPIN_MOVES:
        if has_spikes(boss_state):
            add_delta(deltas, "replay.spin.clears_owned_side", -6)
        else:
            add_delta(deltas, "replay.spin.clean_side", 5)
        if is_ghost(opponent_active):
            add_delta(deltas, "replay.spin.active_spinblocker", 12)
    elif move_key in SELF_KO_MOVES:
        if hp_percent(boss_active.hp) <= 35:
            add_delta(deltas, "replay.cashout.low_support_piece", -4)
        else:
            add_delta(deltas, "replay.cashout.preserve_live_piece", 4)
        if is_ghost(opponent_active) or protected(opponent_active):
            add_delta(deltas, "replay.cashout.named_absorber_or_shield", 10)
    elif move_key in RECOVERY_MOVES:
        if hp_percent(boss_active.hp) <= 55:
            add_delta(deltas, "replay.recovery.low_hp_reset", -5)
        else:
            add_delta(deltas, "replay.recovery.too_early", 3)
    elif move_key in SETUP_MOVES:
        if hp_percent(boss_active.hp) <= 35:
            add_delta(deltas, "replay.setup.too_low", 5)
        else:
            add_delta(deltas, "replay.setup.route_pressure", -3)
        if public_phazer_live(opponent_state):
            add_delta(deltas, "replay.setup.public_phaze_risk", 4)
    elif move_key in PHAZE_MOVES:
        if has_spikes(opponent_state) or boosted(opponent_active):
            add_delta(deltas, "replay.phaze.converts_spikes_or_boost", -5)
        else:
            add_delta(deltas, "replay.phaze.no_named_route", 2)
    elif move_key in PASS_MOVES:
        if boosted(boss_active):
            add_delta(deltas, "replay.pass.boost_handoff", -6)
        else:
            add_delta(deltas, "replay.pass.dry_handoff", 1)
    elif move_key in STATUS_MOVES:
        if opponent_active.status or protected(opponent_active):
            add_delta(deltas, "replay.status.bad_target", 7)
        else:
            add_delta(deltas, "replay.status.live_target", -2)
    else:
        add_delta(deltas, "replay.damage.active_pressure", -1)
        if hp_percent(opponent_active.hp) <= 35:
            add_delta(deltas, "replay.damage.removal_threshold", -3)

    action: dict[str, Any] = {
        "id": action_id("move", name),
        "name": name,
        "kind": "move",
        "policy_tags": sorted(tags),
    }
    if deltas:
        action["deltas"] = deltas
    return action


def action_for_switch(name: str, *, state: ReplayState, side: str) -> dict[str, Any]:
    side_state = state.sides[side]
    incoming = side_state.seen.get(name, MonState())
    deltas: list[dict[str, Any]] = []
    if hp_percent(incoming.hp) <= 35:
        add_delta(deltas, "replay.switch.low_piece_sack", -3)
    else:
        add_delta(deltas, "replay.switch.counter_handoff", -2)
    return {
        "id": action_id("switch", name),
        "name": f"Switch {name}",
        "kind": "switch",
        "deltas": deltas,
        "policy_tags": ["switch_sack", "support_handoff"],
    }


def public_state_for_side(state: ReplayState, boss_side: str) -> dict[str, Any]:
    player_side = "p2" if boss_side == "p1" else "p1"
    return {
        "boss": public_side_state(state.sides[boss_side]),
        "player": public_side_state(state.sides[player_side]),
        "field": {
            "format": f"Gen {state.gen}",
            "tier": state.tier,
        },
    }


def public_side_state(side: SideState) -> dict[str, Any]:
    active = side.seen.get(side.active, MonState())
    return {
        "name": side.name,
        "active": {
            "species": active.species or side.active,
            "nickname": side.active,
            "hp": active.hp,
            "status": active.status or "healthy",
            "boosts": {key: value for key, value in sorted(active.boosts.items()) if value},
            "volatiles": sorted(active.volatiles),
            "revealed_moves": sorted(active.moves),
        },
        "side_conditions": sorted(side.side_conditions),
        "seen": [
            {
                "nickname": nickname,
                "species": mon.species or nickname,
                "hp": mon.hp,
                "status": mon.status or "healthy",
                "revealed_moves": sorted(mon.moves),
            }
            for nickname, mon in sorted(side.seen.items())
        ],
    }


def replay_policy_tags(
    state: ReplayState,
    side: str,
    actions: list[dict[str, Any]],
) -> tuple[set[str], set[str]]:
    boss = state.sides[side]
    opponent = state.sides["p2" if side == "p1" else "p1"]
    policy_tags: set[str] = set()
    condition_tags: set[str] = set()
    for action in actions:
        policy_tags.update(action.get("policy_tags", []))
    if has_spikes(boss) or has_spikes(opponent):
        policy_tags.add("hazard_retention")
        condition_tags.add("public_spikes")
    if public_spinner_live(opponent):
        policy_tags.add("rapid_spin")
        condition_tags.add("opponent_revealed_spinner")
    if public_phazer_live(opponent):
        policy_tags.add("support_handoff")
        condition_tags.add("opponent_revealed_phazer")
    opponent_active = opponent.seen.get(opponent.active, MonState())
    if protected(opponent_active):
        condition_tags.add("protected_target")
    if boosted(opponent_active):
        condition_tags.add("opponent_boosted")
    return policy_tags, condition_tags


def materialize_log_source(source: str | Path) -> tuple[Path, str]:
    source_text = str(source)
    if source_text.startswith(("http://", "https://")):
        url = source_text if source_text.endswith(".log") else source_text.rstrip("/") + ".log"
        with urllib.request.urlopen(url, timeout=30) as response:
            payload = response.read()
        tmp = NamedTemporaryFile(delete=False, suffix=".log")
        tmp.write(payload)
        tmp.close()
        return Path(tmp.name), url
    path = Path(source)
    if not path.exists():
        raise PreferenceDataError(f"replay log does not exist: {path}")
    return path, display_path(path)


def selected_turns(lines: list[str], turns: tuple[int, ...]) -> list[int]:
    available = sorted(turn_line_indexes(lines))
    if not turns:
        return available
    missing = sorted(set(turns) - set(available))
    if missing:
        raise PreferenceDataError("turn(s) not found: " + ", ".join(map(str, missing)))
    return list(turns)


def reached_limit(scenarios: list[dict[str, Any]], limit: int | None) -> bool:
    return limit is not None and len(scenarios) >= limit


def keyword_tags(text: str, table: tuple[tuple[str, tuple[str, ...]], ...]) -> set[str]:
    lower = text.lower()
    return {tag for tag, needles in table if any(needle in lower for needle in needles)}


def family_for_text(text: str) -> str:
    lower = text.lower()
    for family, needles in FAMILY_KEYWORDS:
        if any(needle in lower for needle in needles):
            return family
    return "mastery_policy"


def move_class_tags(name: str) -> set[str]:
    key = name.lower()
    if key in HAZARD_MOVES:
        return {"hazard_retention", "spikes"}
    if key in SPIN_MOVES:
        return {"hazard_retention", "rapid_spin"}
    if key in SELF_KO_MOVES:
        return {"cashout", "route_converter"}
    if key in SETUP_MOVES:
        return {"setup_timing"}
    if key in RECOVERY_MOVES:
        return {"recovery_timing"}
    if key in PHAZE_MOVES:
        return {"support_handoff", "phaze"}
    if key in PASS_MOVES:
        return {"support_handoff", "baton_pass"}
    if key in STATUS_MOVES:
        return {"status_timing"}
    return {"active_pressure"}


def acceptable_action_ids(actions: list[dict[str, Any]], actual: dict[str, str]) -> list[str]:
    actual_tags: set[str] = set()
    actual_id = action_id(actual["kind"], actual["name"])
    for action in actions:
        if action["id"] == actual_id:
            actual_tags = set(action.get("policy_tags", []))
            break
    if not actual_tags:
        return []
    return [
        str(action["id"])
        for action in actions
        if action["id"] != actual_id and actual_tags & set(action.get("policy_tags", []))
    ][:2]


def add_delta(deltas: list[dict[str, Any]], rule: str, delta: int) -> None:
    if delta:
        deltas.append({"rule": rule, "delta": delta})


def has_spikes(side: SideState) -> bool:
    return "Spikes" in side.side_conditions


def public_spinner_live(side: SideState) -> bool:
    return any("Rapid Spin" in mon.moves for mon in side.seen.values())


def public_phazer_live(side: SideState) -> bool:
    return any(mon.moves & {"Roar", "Whirlwind"} for mon in side.seen.values())


def boosted(mon: MonState) -> bool:
    return any(value > 0 for value in mon.boosts.values())


def protected(mon: MonState) -> bool:
    return bool(mon.volatiles & PROTECTION_STATES)


def is_ghost(mon: MonState) -> bool:
    return clean_species(mon.species) in GHOST_SPECIES


def hp_percent(value: str) -> int:
    if not value or value == "?":
        return 100
    if "fnt" in value:
        return 0
    head = value.split()[0]
    if "/" not in head:
        try:
            return int(float(head.rstrip("%")))
        except ValueError:
            return 100
    numerator, denominator = head.split("/", 1)
    try:
        return round(int(numerator) / int(denominator) * 100)
    except (ValueError, ZeroDivisionError):
        return 100


def move_sort_key(name: str) -> tuple[int, str]:
    key = name.lower()
    priority = 5
    if key in HAZARD_MOVES | SPIN_MOVES:
        priority = 0
    elif key in SELF_KO_MOVES:
        priority = 1
    elif key in SETUP_MOVES | RECOVERY_MOVES | PHAZE_MOVES | PASS_MOVES:
        priority = 2
    elif key in STATUS_MOVES:
        priority = 3
    else:
        priority = 4
    return priority, name


def action_id(kind: str, name: str) -> str:
    prefix = "switch" if kind == "switch" else "move"
    return f"{prefix}_{slug(name)}"


def slug(value: str) -> str:
    cleaned = NON_WORD_RE.sub("_", value.lower()).strip("_")
    return cleaned or "unknown"


def replay_scenario_id(
    source_label: str,
    turn: int,
    side: str,
    action_name: str,
    seed: int,
) -> str:
    source_slug = slug(replay_id_for_path_or_text(Path(source_label), source_label) or source_label)
    return f"replay_{source_slug}_{seed}_t{turn:03d}_{side}_{slug(action_name)}"


def replay_id_for_path_or_text(path: Path, text: str) -> str:
    for value in (path.name, text):
        match = REPLAY_ID_RE.search(value)
        if match:
            return match.group(0)
    return ""


def side_for_path(path: Path) -> str:
    match = SIDE_RE.search(path.name)
    return match.group(1) if match else ""


def stable_seed(value: str) -> int:
    return int(scenario_hash({"seed_source": value})[:8], 16)


def restamp_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    cleaned = {
        key: value
        for key, value in scenario.items()
        if key not in {"state_hash", "rom_sha256", "symbols_sha256", "rom", "symbols"}
    }
    return stamp_scenario(cleaned)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("/", "\\")
    except ValueError:
        return str(path)


def empty_batch_report() -> dict[str, Any]:
    return {
        "scenario_count": 0,
        "reviewable_count": 0,
        "verdict_counts": {},
        "policy_tag_counts": {},
        "verdicts": [],
    }


def write_replay_import_report(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def format_replay_import_report(report: dict[str, Any]) -> str:
    batch = report["batch_summary"]
    verdicts = " ".join(
        f"{name}={count}" for name, count in batch["verdict_counts"].items()
    )
    tags = " ".join(
        f"{name}={count}" for name, count in batch["policy_tag_counts"].items()
    )
    return "\n".join(
        [
            "Boss AI replay import",
            (
                f"scenarios={report['scenario_count']} sources={report['source_count']} "
                f"reviewable={batch['reviewable_count']} side={report['side']} mode={report['mode']}"
            ),
            f"verdicts: {verdicts or 'none'}",
            f"review tags: {tags or 'none'}",
        ]
    )


def write_imported_scenarios(scenarios: list[dict[str, Any]], path: Path) -> None:
    write_jsonl(scenarios, path)
