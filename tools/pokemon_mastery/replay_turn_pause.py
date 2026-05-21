#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass
class MonState:
    species: str = ""
    hp: str = "?"
    status: str = ""
    moves: set[str] = field(default_factory=set)
    boosts: dict[str, int] = field(default_factory=dict)
    volatiles: set[str] = field(default_factory=set)
    sleep_source: str = ""
    sleep_actions: int = 0


@dataclass
class SideState:
    name: str = ""
    active: str = "?"
    seen: dict[str, MonState] = field(default_factory=dict)
    side_conditions: set[str] = field(default_factory=set)


@dataclass
class ReplayState:
    gen: str = "?"
    tier: str = "?"
    sides: dict[str, SideState] = field(
        default_factory=lambda: {"p1": SideState(), "p2": SideState()}
    )


DECISION_RELEVANT_VOLATILES = {"Substitute", "confusion", "trapped"}


def split_log_line(line: str) -> list[str]:
    return line.rstrip("\n").split("|")


def side_from_slot(slot: str) -> str:
    return slot[:2]


def side_from_side_label(label: str) -> str:
    return label[:2]


def clean_mon(slot: str) -> str:
    if ": " in slot:
        return slot.split(": ", 1)[1]
    return slot


def clean_species(details: str) -> str:
    return details.split(",", 1)[0]


def parse_hp_status(value: str) -> tuple[str, str]:
    parts = value.split()
    if not parts:
        return "?", ""
    hp = parts[0]
    status = parts[1] if len(parts) > 1 else ""
    return hp, status


def get_mon(state: ReplayState, side: str, mon: str) -> MonState:
    side_state = state.sides[side]
    if mon not in side_state.seen:
        side_state.seen[mon] = MonState()
    return side_state.seen[mon]


def set_status(mon_state: MonState, status: str, source: str = "") -> None:
    mon_state.status = status
    if status == "slp":
        if source:
            mon_state.sleep_source = source
            mon_state.sleep_actions = 0
        elif not mon_state.sleep_source:
            mon_state.sleep_source = "unknown"
    else:
        mon_state.sleep_source = ""
        mon_state.sleep_actions = 0


def apply_event(state: ReplayState, line: str) -> None:
    parts = split_log_line(line)
    if len(parts) < 2:
        return
    tag = parts[1]

    if tag == "player" and len(parts) >= 4:
        side = parts[2]
        if side in state.sides:
            state.sides[side].name = parts[3]
        return
    if tag == "gen" and len(parts) >= 3:
        state.gen = parts[2]
        return
    if tag == "tier" and len(parts) >= 3:
        state.tier = parts[2]
        return
    if tag in {"switch", "drag", "replace"} and len(parts) >= 5:
        side = side_from_slot(parts[2])
        mon = clean_mon(parts[2])
        hp, status = parse_hp_status(parts[4])
        side_state = state.sides[side]
        baton_pass = "[from] Baton Pass" in parts[5:]
        passed_boosts: dict[str, int] = {}
        passed_volatiles: set[str] = set()
        if side_state.active in side_state.seen:
            outgoing_state = side_state.seen[side_state.active]
            if baton_pass:
                passed_boosts = dict(outgoing_state.boosts)
                passed_volatiles = set(outgoing_state.volatiles)
            outgoing_state.boosts = {}
            outgoing_state.volatiles = set()
        side_state.active = mon
        mon_state = get_mon(state, side, mon)
        mon_state.species = clean_species(parts[3])
        mon_state.hp = hp
        set_status(mon_state, status)
        mon_state.boosts = passed_boosts
        mon_state.volatiles = passed_volatiles
        return
    if tag == "move" and len(parts) >= 4:
        side = side_from_slot(parts[2])
        mon = clean_mon(parts[2])
        mon_state = get_mon(state, side, mon)
        mon_state.moves.add(parts[3])
        return
    if tag in {"-damage", "-heal", "-sethp"} and len(parts) >= 4:
        side = side_from_slot(parts[2])
        mon = clean_mon(parts[2])
        hp, status = parse_hp_status(parts[3])
        mon_state = get_mon(state, side, mon)
        mon_state.hp = hp
        set_status(mon_state, status)
        return
    if tag == "-status" and len(parts) >= 4:
        side = side_from_slot(parts[2])
        mon = clean_mon(parts[2])
        source = "Rest" if "[from] move: Rest" in parts[4:] else "move"
        set_status(get_mon(state, side, mon), parts[3], source)
        return
    if tag == "cant" and len(parts) >= 4 and parts[3] == "slp":
        side = side_from_slot(parts[2])
        mon = clean_mon(parts[2])
        mon_state = get_mon(state, side, mon)
        if mon_state.status == "slp":
            mon_state.sleep_actions += 1
        return
    if tag in {"-curestatus", "-cureteam"} and len(parts) >= 3:
        side = side_from_slot(parts[2])
        mon = clean_mon(parts[2])
        set_status(get_mon(state, side, mon), "")
        return
    if tag == "-boost" and len(parts) >= 5:
        side = side_from_slot(parts[2])
        mon = clean_mon(parts[2])
        mon_state = get_mon(state, side, mon)
        mon_state.boosts[parts[3]] = mon_state.boosts.get(parts[3], 0) + int(parts[4])
        return
    if tag == "-unboost" and len(parts) >= 5:
        side = side_from_slot(parts[2])
        mon = clean_mon(parts[2])
        mon_state = get_mon(state, side, mon)
        mon_state.boosts[parts[3]] = mon_state.boosts.get(parts[3], 0) - int(parts[4])
        return
    if tag in {"-clearboost", "-clearallboost"} and len(parts) >= 3:
        side = side_from_slot(parts[2])
        mon = clean_mon(parts[2])
        get_mon(state, side, mon).boosts = {}
        return
    if tag in {"-start", "-end", "-activate"} and len(parts) >= 4:
        effect = parts[3]
        if effect in DECISION_RELEVANT_VOLATILES:
            side = side_from_slot(parts[2])
            mon = clean_mon(parts[2])
            volatiles = get_mon(state, side, mon).volatiles
            if tag in {"-start", "-activate"}:
                volatiles.add(effect)
            else:
                volatiles.discard(effect)
        return
    if tag == "-sidestart" and len(parts) >= 4:
        state.sides[side_from_side_label(parts[2])].side_conditions.add(parts[3])
        return
    if tag == "-sideend" and len(parts) >= 4:
        state.sides[side_from_side_label(parts[2])].side_conditions.discard(parts[3])
        return
    if tag == "faint" and len(parts) >= 3:
        side = side_from_slot(parts[2])
        mon = clean_mon(parts[2])
        mon_state = get_mon(state, side, mon)
        mon_state.hp = "0 fnt"
        set_status(mon_state, "fnt")
        mon_state.volatiles = set()


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def turn_line_indexes(lines: list[str]) -> dict[int, int]:
    indexes: dict[int, int] = {}
    for index, line in enumerate(lines):
        if line.startswith("|turn|"):
            try:
                indexes[int(line.split("|")[2])] = index
            except (IndexError, ValueError):
                continue
    return indexes


def state_before_turn(lines: list[str], turn: int) -> ReplayState:
    indexes = turn_line_indexes(lines)
    if turn not in indexes:
        raise ValueError(f"turn {turn} not found")
    state = ReplayState()
    for line in lines[: indexes[turn]]:
        apply_event(state, line)
    return state


def turn_segment(lines: list[str], turn: int) -> list[str]:
    indexes = turn_line_indexes(lines)
    if turn not in indexes:
        raise ValueError(f"turn {turn} not found")
    start = indexes[turn]
    following = [index for value, index in indexes.items() if value > turn]
    end = min(following) if following else len(lines)
    return lines[start:end]


def format_boosts(boosts: dict[str, int]) -> str:
    active = [f"{stat}{value:+d}" for stat, value in sorted(boosts.items()) if value]
    return ", ".join(active) if active else "none"


def format_volatiles(volatiles: set[str]) -> str:
    return ", ".join(sorted(volatiles))


def format_status(mon_state: MonState) -> str:
    if mon_state.status != "slp":
        return mon_state.status or "healthy"
    if mon_state.sleep_source == "Rest":
        note = f"slp; Rest sleep actions {mon_state.sleep_actions}"
        if mon_state.sleep_actions >= 2:
            note += "; will wake and can act this prompted turn in GSC"
        return note
    return f"slp; sleep actions {mon_state.sleep_actions}"


def format_mon_label(nickname: str, mon_state: MonState) -> str:
    if mon_state.species and mon_state.species != nickname:
        return f"{nickname} ({mon_state.species})"
    return nickname


def format_side(label: str, side: SideState) -> list[str]:
    name = side.name or label
    active_state = side.seen.get(side.active, MonState())
    active_label = format_mon_label(side.active, active_state)
    side_conditions = ", ".join(sorted(side.side_conditions)) or "none"
    lines = [
        (
            f"{label} / {name}: active {active_label} "
            f"HP {active_state.hp} {format_status(active_state)}; "
            + (
                f"volatiles {format_volatiles(active_state.volatiles)}; "
                if active_state.volatiles
                else ""
            )
            + f"boosts {format_boosts(active_state.boosts)}; side {side_conditions}."
        )
    ]
    seen = []
    for mon, mon_state in sorted(side.seen.items()):
        mon_label = format_mon_label(mon, mon_state)
        moves = ", ".join(sorted(mon_state.moves)) if mon_state.moves else "no moves revealed"
        volatile_text = (
            f"; volatiles: {format_volatiles(mon_state.volatiles)}"
            if mon_state.volatiles
            else ""
        )
        seen.append(
            f"{mon_label} {mon_state.hp} {format_status(mon_state)}"
            f"{volatile_text}; moves: {moves}"
        )
    lines.append("Seen: " + (" | ".join(seen) if seen else "none"))
    return lines


def format_prompt(path: Path, turn: int) -> str:
    lines = read_lines(path)
    state = state_before_turn(lines, turn)
    output = [
        f"# Replay Turn-Pause Prompt: {path.name} before Turn {turn}",
        "",
        f"Format: Gen {state.gen}; tier: {state.tier}",
        "Mode: spectator public unless a separate team sheet is supplied.",
        "",
        "Task: recommend each player's move or switch before revealing this turn.",
        "For each side, first give a route transaction: their package -> our absorber/converter -> their next owner -> our punish.",
        "Before ranking, state the critical ledger: sleep/wake counter, passed boosts/speed, self-KO or cash-out branch, and immediate lethal/miss/crit risk.",
        "Before final top action, compare candidates against active target -> next owner -> counter-owner after our handoff.",
        "If recovery, hazards, removal, phazing, or sleep-turn actions can reset the route, compare reset-denial before damage.",
        "Then give top action, confidence, ranked top-three candidates, worst branch, public-info tiers, and fallback.",
        "Route-budget tiebreaker: state why #1 ranks above #2, what public fact would make #2 become #1, and the rejected safe/default line.",
        "Score likely misses with route_budget, resource_identity, reset_loop, script_too_slow, branch_punish, and positive_selection.",
        "",
    ]
    output.extend(format_side("p1", state.sides["p1"]))
    output.append("")
    output.extend(format_side("p2", state.sides["p2"]))
    return "\n".join(output)


def relevant_reveal_line(line: str) -> bool:
    parts = split_log_line(line)
    if len(parts) < 2:
        return False
    return parts[1] in {
        "turn",
        "switch",
        "drag",
        "move",
        "cant",
        "faint",
        "-damage",
        "-heal",
        "-start",
        "-end",
        "-activate",
        "-status",
        "-curestatus",
        "-boost",
        "-unboost",
        "-sidestart",
        "-sideend",
        "-crit",
        "-miss",
        "-supereffective",
        "-resisted",
        "-immune",
    }


def format_reveal(path: Path, turn: int) -> str:
    segment = [line for line in turn_segment(read_lines(path), turn) if relevant_reveal_line(line)]
    return "\n".join(segment)


def format_summary(path: Path) -> str:
    lines = read_lines(path)
    state = ReplayState()
    for line in lines:
        apply_event(state, line)
    indexes = turn_line_indexes(lines)
    turns = sorted(indexes)
    return "\n".join(
        [
            f"Replay: {path}",
            f"Format: Gen {state.gen}; tier: {state.tier}",
            f"Players: p1={state.sides['p1'].name or '?'}; p2={state.sides['p2'].name or '?'}",
            f"Turns: {turns[0] if turns else '?'}-{turns[-1] if turns else '?'} ({len(turns)} turns)",
        ]
    )


def side_known_roster(lines: list[str], side: str) -> dict[str, MonState]:
    roster: dict[str, MonState] = {}
    for line in lines:
        parts = split_log_line(line)
        if len(parts) < 2:
            continue
        tag = parts[1]
        if tag in {"switch", "drag", "replace"} and len(parts) >= 5:
            if side_from_slot(parts[2]) != side:
                continue
            mon = clean_mon(parts[2])
            mon_state = roster.setdefault(mon, MonState())
            mon_state.species = clean_species(parts[3])
        elif tag == "move" and len(parts) >= 4:
            if side_from_slot(parts[2]) != side:
                continue
            mon = clean_mon(parts[2])
            mon_state = roster.setdefault(mon, MonState())
            mon_state.moves.add(parts[3])
    return roster


def format_side_known_roster(lines: list[str], side: str) -> list[str]:
    roster = side_known_roster(lines, side)
    output = [
        (
            f"Side-known reconstruction for {side}: own roster and moves "
            "eventually shown in this replay only; unused moves may be missing."
        )
    ]
    if not roster:
        output.append("Own side-known roster: none reconstructed.")
        return output
    entries = []
    for mon, mon_state in sorted(roster.items()):
        mon_label = format_mon_label(mon, mon_state)
        moves = ", ".join(sorted(mon_state.moves)) if mon_state.moves else "no moves shown"
        entries.append(f"{mon_label}; own shown moves: {moves}")
    output.append("Own side-known roster: " + " | ".join(entries))
    return output


def format_side_prompt(path: Path, turn: int, advise_side: str) -> str:
    if advise_side not in {"p1", "p2"}:
        raise ValueError("advise side must be p1 or p2")
    lines = read_lines(path)
    state = state_before_turn(lines, turn)
    side_name = state.sides[advise_side].name or advise_side
    output = [
        f"# Replay Side-Known Prompt: {path.name} before Turn {turn}",
        "",
        f"Format: Gen {state.gen}; tier: {state.tier}",
        f"Mode: side-known reconstructed for {advise_side} / {side_name}.",
        "Opponent information remains spectator-public; do not infer hidden opponent team, moves, or items.",
        "",
        f"Task: recommend only {advise_side}'s move or switch before revealing this turn.",
        "First give a route transaction: their package -> our absorber/converter -> their next owner -> our punish.",
        "Before ranking, state the critical ledger: sleep/wake counter, passed boosts/speed, self-KO or cash-out branch, and immediate lethal/miss/crit risk.",
        "Before final top action, compare candidates against active target -> next owner -> counter-owner after our handoff.",
        "If recovery, hazards, removal, phazing, or sleep-turn actions can reset the route, compare reset-denial before damage.",
        "Then give top action, confidence, ranked top-three candidates, worst branch, public-info tiers, and fallback.",
        "Route-budget tiebreaker: state why #1 ranks above #2, what public fact would make #2 become #1, and the rejected safe/default line.",
        "Score likely misses with route_budget, resource_identity, reset_loop, script_too_slow, branch_punish, and positive_selection.",
        "",
    ]
    output.extend(format_side_known_roster(lines, advise_side))
    output.append("")
    output.extend(format_side("p1", state.sides["p1"]))
    output.append("")
    output.extend(format_side("p2", state.sides["p2"]))
    return "\n".join(output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Reveal Pokemon Showdown replay logs one turn at a time for practice."
    )
    parser.add_argument("log", type=Path, help="Pokemon Showdown raw .log file")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("summary", help="print replay metadata")

    prompt = subparsers.add_parser("prompt", help="print public state before a turn")
    prompt.add_argument("--turn", type=int, required=True)

    side_prompt = subparsers.add_parser(
        "side-prompt",
        help="print public state plus one advised side's reconstructed own information",
    )
    side_prompt.add_argument("--turn", type=int, required=True)
    side_prompt.add_argument("--side", choices=["p1", "p2"], required=True)

    reveal = subparsers.add_parser("reveal", help="print actual events for a turn")
    reveal.add_argument("--turn", type=int, required=True)

    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "summary":
        print(format_summary(args.log))
    elif args.command == "prompt":
        print(format_prompt(args.log, args.turn))
    elif args.command == "side-prompt":
        print(format_side_prompt(args.log, args.turn, args.side))
    elif args.command == "reveal":
        print(format_reveal(args.log, args.turn))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
