#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PARTIES_FILE = ROOT / "data" / "trainers" / "parties.asm"

TARGET_GROUPS = {
    "FalknerGroup",
    "WhitneyGroup",
    "BugsyGroup",
    "MortyGroup",
    "PryceGroup",
    "JasmineGroup",
    "ChuckGroup",
    "ClairGroup",
    "WillGroup",
    "BrunoGroup",
    "KarenGroup",
    "KogaGroup",
    "ChampionGroup",
    "BrockGroup",
    "MistyGroup",
    "LtSurgeGroup",
    "ErikaGroup",
    "JanineGroup",
    "SabrinaGroup",
    "BlaineGroup",
    "BlueGroup",
    "RedGroup",
    "Rival1Group",
    "Rival2Group",
}

GROUP_RE = re.compile(r"^([A-Za-z0-9_]+Group):\s*$")
COMMENT_RE = re.compile(r"^\s*;\s*([A-Z0-9_?]+)\s+\((\d+)\)\s*$")
TRAINER_RE = re.compile(r'^\s*db\s+"[^"]*@",\s*(TRAINERTYPE_[A-Z_]+)\s*(?:;.*)?$')
DB_RE = re.compile(r"^\s*db\s+(.+?)\s*(?:;.*)?$")


@dataclass(frozen=True)
class Mon:
    species: str
    moves: tuple[str, str, str, str]


@dataclass
class Entry:
    group: str
    index: int
    label: str
    trainer_type: str
    mons: list[Mon]


def _split_tokens(raw_db_payload: str) -> list[str]:
    return [token.strip() for token in raw_db_payload.split(",")]


def parse_parties(path: Path) -> list[Entry]:
    if not path.exists():
        raise FileNotFoundError(path)

    entries: list[Entry] = []
    current_group: str | None = None
    pending_label: str | None = None
    index_by_group: dict[str, int] = {}
    active_entry: Entry | None = None

    for line_no, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        group_match = GROUP_RE.match(raw_line)
        if group_match:
            current_group = group_match.group(1)
            pending_label = None
            active_entry = None
            index_by_group.setdefault(current_group, 0)
            continue

        if current_group is None:
            continue

        comment_match = COMMENT_RE.match(raw_line)
        if comment_match:
            pending_label = f"{comment_match.group(1)} ({comment_match.group(2)})"
            continue

        trainer_match = TRAINER_RE.match(raw_line)
        if trainer_match:
            if active_entry is not None:
                raise ValueError(f"{path}:{line_no}: trainer header before previous trainer terminated")
            index_by_group[current_group] += 1
            entry_index = index_by_group[current_group]
            active_entry = Entry(
                group=current_group,
                index=entry_index,
                label=pending_label or f"{current_group} ({entry_index})",
                trainer_type=trainer_match.group(1),
                mons=[],
            )
            pending_label = None
            entries.append(active_entry)
            continue

        if active_entry is None:
            continue

        db_match = DB_RE.match(raw_line)
        if not db_match:
            continue

        tokens = _split_tokens(db_match.group(1))
        if not tokens:
            continue
        if tokens[0] == "-1":
            active_entry = None
            continue

        trainer_type = active_entry.trainer_type
        if trainer_type == "TRAINERTYPE_MOVES":
            if len(tokens) != 6:
                raise ValueError(f"{path}:{line_no}: expected 6 tokens for TRAINERTYPE_MOVES, got {len(tokens)}")
            species = tokens[1]
            moves = (tokens[2], tokens[3], tokens[4], tokens[5])
        elif trainer_type == "TRAINERTYPE_ITEM_MOVES":
            if len(tokens) != 7:
                raise ValueError(
                    f"{path}:{line_no}: expected 7 tokens for TRAINERTYPE_ITEM_MOVES, got {len(tokens)}"
                )
            species = tokens[1]
            moves = (tokens[3], tokens[4], tokens[5], tokens[6])
        elif trainer_type == "TRAINERTYPE_NORMAL":
            if len(tokens) != 2:
                raise ValueError(f"{path}:{line_no}: expected 2 tokens for TRAINERTYPE_NORMAL, got {len(tokens)}")
            species = tokens[1]
            moves = ("", "", "", "")
        elif trainer_type == "TRAINERTYPE_ITEM":
            if len(tokens) != 3:
                raise ValueError(f"{path}:{line_no}: expected 3 tokens for TRAINERTYPE_ITEM, got {len(tokens)}")
            species = tokens[1]
            moves = ("", "", "", "")
        else:
            raise ValueError(f"{path}:{line_no}: unknown trainer type: {trainer_type}")

        active_entry.mons.append(Mon(species=species, moves=moves))

    return entries


def main() -> int:
    try:
        entries = parse_parties(PARTIES_FILE)
    except Exception as exc:
        print(f"ERROR|parse_failed|{exc}", file=sys.stderr)
        return 1

    targeted = [entry for entry in entries if entry.group in TARGET_GROUPS]
    failures: list[str] = []
    mon_count = 0

    for entry in targeted:
        if entry.trainer_type not in {"TRAINERTYPE_MOVES", "TRAINERTYPE_ITEM_MOVES"}:
            failures.append(
                f"ERROR|missing_explicit_moves|{entry.group}|{entry.index}|{entry.label}|{entry.trainer_type}"
            )
            continue

        for slot, mon in enumerate(entry.mons, start=1):
            mon_count += 1
            for move_slot, move in enumerate(mon.moves, start=1):
                if not move:
                    failures.append(
                        f"ERROR|empty_move|{entry.group}|{entry.index}|slot{slot}|{mon.species}|move{move_slot}"
                    )
                elif move == "NO_MOVE":
                    failures.append(
                        f"ERROR|no_move_token|{entry.group}|{entry.index}|slot{slot}|{mon.species}|move{move_slot}"
                    )

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        print(f"FAIL|entries={len(targeted)}|mons={mon_count}|issues={len(failures)}", file=sys.stderr)
        return 1

    print(f"OK|entries={len(targeted)}|mons={mon_count}|no_no_move_tokens=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
