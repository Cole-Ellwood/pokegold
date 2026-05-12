from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


GROUP_RE = re.compile(r"^([A-Za-z0-9_]+Group):\s*$")
COMMENT_RE = re.compile(r"^\s*;\s*([A-Z0-9_?\.]+)\s+\((\d+)\)\s*$")
TRAINER_RE = re.compile(r'^\s*db\s+"[^"]*@",\s*(TRAINERTYPE_[A-Z_]+)\s*(?:;.*)?$')
DB_RE = re.compile(r"^\s*db\s+(.+?)\s*(?:;.*)?$")


@dataclass(frozen=True)
class TrainerPartyMon:
    level: int
    species: str
    item: str
    moves: tuple[str, ...]
    line_no: int


@dataclass
class TrainerPartyEntry:
    group: str
    index: int
    label: str
    trainer_type: str
    line_no: int
    mons: list[TrainerPartyMon]


def split_tokens(raw_db_payload: str) -> list[str]:
    return [token.strip() for token in raw_db_payload.split(",")]


def parse_parties(path: Path) -> list[TrainerPartyEntry]:
    if not path.exists():
        raise FileNotFoundError(path)
    return parse_parties_text(path.read_text(encoding="utf-8"), path_label=str(path))


def parse_parties_text(text: str, *, path_label: str = "parties.asm") -> list[TrainerPartyEntry]:
    entries: list[TrainerPartyEntry] = []
    current_group: str | None = None
    pending_label: str | None = None
    index_by_group: dict[str, int] = {}
    active_entry: TrainerPartyEntry | None = None

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
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
                raise ValueError(f"{path_label}:{line_no}: trainer header before previous trainer terminated")
            index_by_group[current_group] += 1
            entry_index = index_by_group[current_group]
            active_entry = TrainerPartyEntry(
                group=current_group,
                index=entry_index,
                label=pending_label or f"{current_group} ({entry_index})",
                trainer_type=trainer_match.group(1),
                line_no=line_no,
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

        tokens = split_tokens(db_match.group(1))
        if not tokens:
            continue
        if tokens[0] == "-1":
            active_entry = None
            continue

        level, species, item, moves = parse_mon_tokens(
            path_label,
            line_no,
            active_entry.trainer_type,
            tokens,
        )
        active_entry.mons.append(
            TrainerPartyMon(
                level=level,
                species=species,
                item=item,
                moves=moves,
                line_no=line_no,
            )
        )

    return entries


def parse_mon_tokens(
    path_label: str,
    line_no: int,
    trainer_type: str,
    tokens: list[str],
) -> tuple[int, str, str, tuple[str, ...]]:
    if trainer_type == "TRAINERTYPE_ITEM_MOVES":
        if len(tokens) != 7:
            raise ValueError(f"{path_label}:{line_no}: expected 7 tokens for TRAINERTYPE_ITEM_MOVES, got {len(tokens)}")
        return int(tokens[0]), tokens[1], tokens[2], tuple(tokens[3:7])
    if trainer_type == "TRAINERTYPE_ITEM":
        if len(tokens) != 3:
            raise ValueError(f"{path_label}:{line_no}: expected 3 tokens for TRAINERTYPE_ITEM, got {len(tokens)}")
        return int(tokens[0]), tokens[1], tokens[2], ()
    if trainer_type == "TRAINERTYPE_MOVES":
        if len(tokens) != 6:
            raise ValueError(f"{path_label}:{line_no}: expected 6 tokens for TRAINERTYPE_MOVES, got {len(tokens)}")
        return int(tokens[0]), tokens[1], "", tuple(tokens[2:6])
    if trainer_type == "TRAINERTYPE_NORMAL":
        if len(tokens) != 2:
            raise ValueError(f"{path_label}:{line_no}: expected 2 tokens for TRAINERTYPE_NORMAL, got {len(tokens)}")
        return int(tokens[0]), tokens[1], "", ()
    raise ValueError(f"{path_label}:{line_no}: unknown trainer type: {trainer_type}")


def entry_key(entry: TrainerPartyEntry) -> tuple[str, int]:
    return (entry.group, entry.index)
