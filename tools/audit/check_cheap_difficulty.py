#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from trainer_parties import TrainerPartyEntry, entry_key, parse_parties


ROOT = Path(__file__).resolve().parents[2]
PARTIES_FILE = ROOT / "data" / "trainers" / "parties.asm"


TARGET_TIERS: dict[tuple[str, int], str] = {
    ("FalknerGroup", 1): "EARLY",
    ("BugsyGroup", 1): "EARLY",
    ("WhitneyGroup", 1): "EARLY",
    ("MortyGroup", 1): "MID",
    ("ChuckGroup", 1): "MID",
    ("JasmineGroup", 1): "MID",
    ("PryceGroup", 1): "LATE",
    ("ClairGroup", 1): "LATE",
    ("WillGroup", 1): "LATE",
    ("BrunoGroup", 1): "LATE",
    ("KogaGroup", 1): "LATE",
    ("KarenGroup", 1): "LATE",
    ("ChampionGroup", 1): "LATE",
    ("BrockGroup", 1): "LATE",
    ("MistyGroup", 1): "LATE",
    ("LtSurgeGroup", 1): "LATE",
    ("ErikaGroup", 1): "LATE",
    ("JanineGroup", 1): "LATE",
    ("SabrinaGroup", 1): "LATE",
    ("BlaineGroup", 1): "LATE",
    ("BlueGroup", 1): "LATE",
    ("RedGroup", 1): "LATE",
    **{("Rival1Group", index): "EARLY" for index in range(1, 7)},
    **{("Rival1Group", index): "MID" for index in range(7, 13)},
    **{("Rival1Group", index): "LATE" for index in range(13, 16)},
    **{("Rival2Group", index): "LATE" for index in range(1, 7)},
}

NO_ITEM_ALLOWLIST = {
    ("Rival1Group", 1),
    ("Rival1Group", 2),
    ("Rival1Group", 3),
    ("Rival1Group", 4),
    ("Rival1Group", 5),
    ("Rival1Group", 6),
}

EARLY_FORBIDDEN_ITEMS = {
    "AIR_BALLOON",
    "ASSAULT_VEST",
    "CHOICE_BAND",
    "CHOICE_SCARF",
    "CHOICE_SPECS",
    "EXPERT_BELT",
    "LEFTOVERS",
    "LIFE_ORB",
    "LIGHT_BALL",
    "MUSCLE_BAND",
    "ROCKY_HELMET",
    "WISE_GLASSES",
}

CHOICE_ITEMS = {"CHOICE_BAND", "CHOICE_SCARF", "CHOICE_SPECS"}
LATE_SPIKE_ITEMS = {"ASSAULT_VEST", "LIFE_ORB"}
ONE_OFF_ITEMS = {"LIGHT_BALL": ("RedGroup", 1)}

JOHTO_GYM_ORDER = (
    ("FalknerGroup", 1),
    ("BugsyGroup", 1),
    ("WhitneyGroup", 1),
    ("MortyGroup", 1),
    ("ChuckGroup", 1),
    ("JasmineGroup", 1),
    ("PryceGroup", 1),
    ("ClairGroup", 1),
)

RIVAL_BRANCH_SETS = (
    (("Rival1Group", 1), ("Rival1Group", 2), ("Rival1Group", 3)),
    (("Rival1Group", 4), ("Rival1Group", 5), ("Rival1Group", 6)),
    (("Rival1Group", 7), ("Rival1Group", 8), ("Rival1Group", 9)),
    (("Rival1Group", 10), ("Rival1Group", 11), ("Rival1Group", 12)),
    (("Rival1Group", 13), ("Rival1Group", 14), ("Rival1Group", 15)),
    (("Rival2Group", 1), ("Rival2Group", 2), ("Rival2Group", 3)),
    (("Rival2Group", 4), ("Rival2Group", 5), ("Rival2Group", 6)),
)


def fail(failures: list[str], message: str) -> None:
    failures.append(f"ERROR|{message}")


def check_target_coverage(targeted: dict[tuple[str, int], TrainerPartyEntry], failures: list[str]) -> None:
    missing = sorted(set(TARGET_TIERS) - set(targeted))
    for group, index in missing:
        fail(failures, f"missing_target|{group}|{index}")


def check_item_pressure(targeted: dict[tuple[str, int], TrainerPartyEntry], failures: list[str]) -> None:
    for key, entry in sorted(targeted.items()):
        tier = TARGET_TIERS[key]
        for slot, mon in enumerate(entry.mons, start=1):
            item = mon.item
            if not item:
                fail(failures, f"missing_item_schema|{entry.group}|{entry.index}|slot{slot}|{mon.species}")
                continue
            if item == "NO_ITEM" and key not in NO_ITEM_ALLOWLIST:
                fail(failures, f"unexpected_no_item|{entry.group}|{entry.index}|slot{slot}|{mon.species}")
            if tier == "EARLY" and item in EARLY_FORBIDDEN_ITEMS:
                fail(failures, f"early_late_item|{entry.group}|{entry.index}|slot{slot}|{mon.species}|{item}")
            if item in CHOICE_ITEMS and (tier != "LATE" or mon.level < 38):
                fail(failures, f"choice_item_too_early|{entry.group}|{entry.index}|slot{slot}|L{mon.level}|{mon.species}|{item}")
            if item in LATE_SPIKE_ITEMS and tier != "LATE":
                fail(failures, f"late_spike_item_before_late_tier|{entry.group}|{entry.index}|slot{slot}|{mon.species}|{item}")
            if item in ONE_OFF_ITEMS and key != ONE_OFF_ITEMS[item]:
                allowed_group, allowed_index = ONE_OFF_ITEMS[item]
                fail(
                    failures,
                    "one_off_item_wrong_owner|"
                    f"{entry.group}|{entry.index}|slot{slot}|{mon.species}|{item}|"
                    f"expected={allowed_group}:{allowed_index}",
                )


def check_party_size_by_tier(targeted: dict[tuple[str, int], TrainerPartyEntry], failures: list[str]) -> None:
    for key, entry in sorted(targeted.items()):
        tier = TARGET_TIERS[key]
        mon_count = len(entry.mons)
        if tier == "EARLY" and mon_count > 3:
            fail(failures, f"early_party_too_large|{entry.group}|{entry.index}|mons={mon_count}")
        if tier == "MID" and mon_count > 5:
            fail(failures, f"mid_party_too_large|{entry.group}|{entry.index}|mons={mon_count}")
        if tier == "LATE" and mon_count > 6:
            fail(failures, f"late_party_too_large|{entry.group}|{entry.index}|mons={mon_count}")


def check_johto_curve(targeted: dict[tuple[str, int], TrainerPartyEntry], failures: list[str]) -> list[int]:
    max_levels: list[int] = []
    for key in JOHTO_GYM_ORDER:
        entry = targeted.get(key)
        if entry is None:
            continue
        max_levels.append(max(mon.level for mon in entry.mons))

    for index, (previous, current) in enumerate(zip(max_levels, max_levels[1:]), start=2):
        delta = current - previous
        # Mid-Johto (Chuck/Jasmine/Pryce) shares a flat 34 cap because the three
        # gyms are reachable in any order; the Morty->Chuck step is intentionally
        # the segment's full ramp (26->34 = 8) so the EXP cap can plateau across
        # the segment. Tighten back if the segment design changes.
        if delta > 8:
            fail(failures, f"johto_gym_level_jump_too_large|badge_index={index}|{previous}->{current}|delta={delta}")
        if delta < -1:
            fail(failures, f"johto_gym_level_drop_too_large|badge_index={index}|{previous}->{current}|delta={delta}")
    if max_levels and max_levels[0] > 14:
        fail(failures, f"falkner_peak_too_high|peak={max_levels[0]}")
    if max_levels and max_levels[-1] > 40:
        fail(failures, f"clair_peak_too_high|peak={max_levels[-1]}")
    return max_levels


def check_rival_branch_parity(targeted: dict[tuple[str, int], TrainerPartyEntry], failures: list[str]) -> None:
    for branch_set in RIVAL_BRANCH_SETS:
        entries = [targeted.get(key) for key in branch_set]
        if any(entry is None for entry in entries):
            continue
        concrete = [entry for entry in entries if entry is not None]
        signatures = [
            (
                len(entry.mons),
                tuple(mon.level for mon in entry.mons),
                tuple(mon.item == "NO_ITEM" for mon in entry.mons),
            )
            for entry in concrete
        ]
        if len(set(signatures)) > 1:
            labels = ",".join(f"{entry.group}:{entry.index}:{entry.label}" for entry in concrete)
            fail(failures, f"rival_branch_pressure_mismatch|{labels}|signatures={signatures}")


def main() -> int:
    try:
        entries = parse_parties(PARTIES_FILE)
    except Exception as exc:
        print(f"ERROR|parse_failed|{exc}", file=sys.stderr)
        return 1

    targeted = {entry_key(entry): entry for entry in entries if entry_key(entry) in TARGET_TIERS}
    failures: list[str] = []

    check_target_coverage(targeted, failures)
    check_item_pressure(targeted, failures)
    check_party_size_by_tier(targeted, failures)
    max_levels = check_johto_curve(targeted, failures)
    check_rival_branch_parity(targeted, failures)

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        print(f"FAIL|cheap_difficulty_issues={len(failures)}", file=sys.stderr)
        return 1

    mon_count = sum(len(entry.mons) for entry in targeted.values())
    print("Cheap difficulty audit passed.")
    print(f"Target entries checked: {len(targeted)}")
    print(f"Target mons checked: {mon_count}")
    print("Sentinels:")
    print("  - early-tier late-item leakage")
    print("  - Choice item timing")
    print("  - Life Orb/Assault Vest tier timing")
    print("  - one-off Light Ball ownership")
    print("  - party-size pressure by tier")
    print("  - Rival starter-branch pressure parity")
    print("  - Johto gym level curve")
    print("Johto gym peak levels: " + ", ".join(str(level) for level in max_levels))
    print("Rival branch sets checked: " + str(len(RIVAL_BRANCH_SETS)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
