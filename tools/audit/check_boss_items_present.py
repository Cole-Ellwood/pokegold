#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from trainer_parties import parse_parties


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

# NO_ITEM is allowed only for explicitly documented low-band rival encounters.
NO_ITEM_ALLOWLIST: dict[tuple[str, int], str] = {
    ("Rival1Group", 1): "Starter theft opener: no held item to preserve tutorial readability.",
    ("Rival1Group", 2): "Starter theft opener: no held item to preserve tutorial readability.",
    ("Rival1Group", 3): "Starter theft opener: no held item to preserve tutorial readability.",
    ("Rival1Group", 4): "Azalea rival branch kept itemless to avoid overtuning the first multi-mon rival gate.",
    ("Rival1Group", 5): "Azalea rival branch kept itemless to avoid overtuning the first multi-mon rival gate.",
    ("Rival1Group", 6): "Azalea rival branch kept itemless to avoid overtuning the first multi-mon rival gate.",
}


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
        if entry.trainer_type not in {"TRAINERTYPE_ITEM", "TRAINERTYPE_ITEM_MOVES"}:
            failures.append(
                f"ERROR|missing_item_schema|{entry.group}|{entry.index}|{entry.label}|{entry.trainer_type}"
            )
            continue

        for slot, mon in enumerate(entry.mons, start=1):
            mon_count += 1
            if not mon.item:
                failures.append(f"ERROR|missing_item|{entry.group}|{entry.index}|slot{slot}|{mon.species}")
                continue

            if mon.item == "NO_ITEM" and (entry.group, entry.index) not in NO_ITEM_ALLOWLIST:
                failures.append(f"ERROR|no_item_not_allowlisted|{entry.group}|{entry.index}|slot{slot}|{mon.species}")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        print(f"FAIL|entries={len(targeted)}|mons={mon_count}|issues={len(failures)}", file=sys.stderr)
        return 1

    print(f"OK|entries={len(targeted)}|mons={mon_count}|items_present=true")
    print("NO_ITEM_ALLOWLIST|group|entry_index|justification")
    for (group, index), justification in sorted(NO_ITEM_ALLOWLIST.items()):
        print(f"NO_ITEM_ALLOWLIST|{group}|{index}|{justification}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
