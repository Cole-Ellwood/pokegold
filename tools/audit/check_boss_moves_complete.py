#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from trainer_parties import TrainerPartyEntry, TrainerPartyMon, parse_parties


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


# NO_MOVE is allowed only for explicitly documented low-band encounters whose
# limited movesets are intentional pacing, not incomplete boss data.
NO_MOVE_ALLOWLIST: dict[tuple[str, int, int, str, int], str] = {
    ("FalknerGroup", 1, 2, "SPEAROW", 3): "Early gym slot kept to two moves for opening-boss readability.",
    ("FalknerGroup", 1, 2, "SPEAROW", 4): "Early gym slot kept to two moves for opening-boss readability.",
    ("Rival1Group", 1, 1, "CHIKORITA", 3): "Starter theft opener: two-move tutorial fight.",
    ("Rival1Group", 1, 1, "CHIKORITA", 4): "Starter theft opener: two-move tutorial fight.",
    ("Rival1Group", 2, 1, "CYNDAQUIL", 3): "Starter theft opener: two-move tutorial fight.",
    ("Rival1Group", 2, 1, "CYNDAQUIL", 4): "Starter theft opener: two-move tutorial fight.",
    ("Rival1Group", 3, 1, "TOTODILE", 3): "Starter theft opener: two-move tutorial fight.",
    ("Rival1Group", 3, 1, "TOTODILE", 4): "Starter theft opener: two-move tutorial fight.",
}


def allowed_no_move(entry: TrainerPartyEntry, slot: int, mon: TrainerPartyMon, move_slot: int) -> bool:
    key = (entry.group, entry.index, slot, mon.species, move_slot)
    return key in NO_MOVE_ALLOWLIST


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
                elif move == "NO_MOVE" and not allowed_no_move(entry, slot, mon, move_slot):
                    failures.append(
                        f"ERROR|no_move_token|{entry.group}|{entry.index}|slot{slot}|{mon.species}|move{move_slot}"
                    )

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        print(f"FAIL|entries={len(targeted)}|mons={mon_count}|issues={len(failures)}", file=sys.stderr)
        return 1

    print(f"OK|entries={len(targeted)}|mons={mon_count}|no_move_allowlisted={len(NO_MOVE_ALLOWLIST)}")
    print("NO_MOVE_ALLOWLIST|group|entry_index|slot|species|move_slot|justification")
    for (group, index, slot, species, move_slot), justification in sorted(NO_MOVE_ALLOWLIST.items()):
        print(f"NO_MOVE_ALLOWLIST|{group}|{index}|slot{slot}|{species}|move{move_slot}|{justification}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
