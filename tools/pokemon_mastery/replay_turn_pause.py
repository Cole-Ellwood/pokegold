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
        state.sides[side].active = mon
        mon_state = get_mon(state, side, mon)
        mon_state.species = clean_species(parts[3])
        mon_state.hp = hp
        mon_state.status = status
        mon_state.boosts = {}
        return
    if tag == "move" and len(parts) >= 4:
        side = side_from_slot(parts[2])
        mon = clean_mon(parts[2])
        get_mon(state, side, mon).moves.add(parts[3])
        return
    if tag in {"-damage", "-heal", "-sethp"} and len(parts) >= 4:
        side = side_from_slot(parts[2])
        mon = clean_mon(parts[2])
        hp, status = parse_hp_status(parts[3])
        mon_state = get_mon(state, side, mon)
        mon_state.hp = hp
        mon_state.status = status
        return
    if tag == "-status" and len(parts) >= 4:
        side = side_from_slot(parts[2])
        mon = clean_mon(parts[2])
        get_mon(state, side, mon).status = parts[3]
        return
    if tag in {"-curestatus", "-cureteam"} and len(parts) >= 3:
        side = side_from_slot(parts[2])
        mon = clean_mon(parts[2])
        get_mon(state, side, mon).status = ""
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
        mon_state.status = "fnt"


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
            f"HP {active_state.hp} {active_state.status or 'healthy'}; "
            f"boosts {format_boosts(active_state.boosts)}; side {side_conditions}."
        )
    ]
    seen = []
    for mon, mon_state in sorted(side.seen.items()):
        mon_label = format_mon_label(mon, mon_state)
        moves = ", ".join(sorted(mon_state.moves)) if mon_state.moves else "no moves revealed"
        seen.append(f"{mon_label} {mon_state.hp} {mon_state.status or 'healthy'}; moves: {moves}")
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
        "For each side, give top action, confidence, serious alternatives, and worst plausible branch.",
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Reveal Pokemon Showdown replay logs one turn at a time for practice."
    )
    parser.add_argument("log", type=Path, help="Pokemon Showdown raw .log file")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("summary", help="print replay metadata")

    prompt = subparsers.add_parser("prompt", help="print public state before a turn")
    prompt.add_argument("--turn", type=int, required=True)

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
    elif args.command == "reveal":
        print(format_reveal(args.log, args.turn))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
