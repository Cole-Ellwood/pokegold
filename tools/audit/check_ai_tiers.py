#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AI_TIERS_FILE = ROOT / "data" / "trainers" / "ai_tiers.asm"
LEADERS_FILE = ROOT / "data" / "trainers" / "leaders.asm"
MOVE_AI_FILE = ROOT / "engine" / "battle" / "ai" / "move.asm"
BOSS_AI_FILE = ROOT / "engine" / "battle" / "ai" / "boss.asm"
TRAINER_ATTRIBUTES_FILE = ROOT / "engine" / "battle" / "read_trainer_attributes.asm"

JOHTO_LEADERS = {
    ("FALKNER", "FALKNER1"),
    ("BUGSY", "BUGSY1"),
    ("WHITNEY", "WHITNEY1"),
    ("MORTY", "MORTY1"),
    ("CHUCK", "CHUCK1"),
    ("JASMINE", "JASMINE1"),
    ("PRYCE", "PRYCE1"),
    ("CLAIR", "CLAIR1"),
}

KANTO_LEADERS = {
    ("BROCK", "BROCK1"),
    ("MISTY", "MISTY1"),
    ("LT_SURGE", "LT_SURGE1"),
    ("ERIKA", "ERIKA1"),
    ("JANINE", "JANINE1"),
    ("SABRINA", "SABRINA1"),
    ("BLAINE", "BLAINE1"),
    ("BLUE", "BLUE1"),
}

RIVAL1_IDS = {
    "RIVAL1_1_CHIKORITA",
    "RIVAL1_1_CYNDAQUIL",
    "RIVAL1_1_TOTODILE",
    "RIVAL1_2_CHIKORITA",
    "RIVAL1_2_CYNDAQUIL",
    "RIVAL1_2_TOTODILE",
    "RIVAL1_3_CHIKORITA",
    "RIVAL1_3_CYNDAQUIL",
    "RIVAL1_3_TOTODILE",
    "RIVAL1_4_CHIKORITA",
    "RIVAL1_4_CYNDAQUIL",
    "RIVAL1_4_TOTODILE",
    "RIVAL1_5_CHIKORITA",
    "RIVAL1_5_CYNDAQUIL",
    "RIVAL1_5_TOTODILE",
}

RIVAL2_IDS = {
    "RIVAL2_1_CHIKORITA",
    "RIVAL2_1_CYNDAQUIL",
    "RIVAL2_1_TOTODILE",
    "RIVAL2_2_CHIKORITA",
    "RIVAL2_2_CYNDAQUIL",
    "RIVAL2_2_TOTODILE",
}

ELITE_FOUR_AND_CHAMPION = {
    ("WILL", "WILL1"),
    ("BRUNO", "BRUNO1"),
    ("KOGA", "KOGA1"),
    ("KAREN", "KAREN1"),
    ("CHAMPION", "LANCE"),
}

POSTGAME_BOSSES = {
    ("RED", "RED1"),
}

ADAPTIVE_LEAD_TARGETS = {
    ("CHUCK", "CHUCK1"),
    ("JASMINE", "JASMINE1"),
    ("PRYCE", "PRYCE1"),
    ("CLAIR", "CLAIR1"),
    ("WILL", "WILL1"),
    ("BRUNO", "BRUNO1"),
    ("KOGA", "KOGA1"),
    ("KAREN", "KAREN1"),
    ("CHAMPION", "LANCE"),
    ("BROCK", "BROCK1"),
    ("MISTY", "MISTY1"),
    ("LT_SURGE", "LT_SURGE1"),
    ("ERIKA", "ERIKA1"),
    ("JANINE", "JANINE1"),
    ("SABRINA", "SABRINA1"),
    ("BLAINE", "BLAINE1"),
    ("BLUE", "BLUE1"),
}

TARGETS = (
    JOHTO_LEADERS
    | KANTO_LEADERS
    | {("RIVAL1", trainer_id) for trainer_id in RIVAL1_IDS}
    | {("RIVAL2", trainer_id) for trainer_id in RIVAL2_IDS}
    | ELITE_FOUR_AND_CHAMPION
    | POSTGAME_BOSSES
)

NONZERO_TIERS = {"AI_TIER_EARLY", "AI_TIER_MID", "AI_TIER_LATE"}

ENTRY_RE = re.compile(
    r"^\s*db\s+([A-Z0-9_]+)\s*,\s*([A-Z0-9_]+)\s*,\s*([A-Z0-9_]+)\s*(?:;.*)?$"
)
PAIR_ENTRY_RE = re.compile(
    r"^\s*db\s+([A-Z0-9_]+)\s*,\s*([A-Z0-9_]+)\s*(?:;.*)?$"
)
CLASS_ENTRY_RE = re.compile(r"^\s*db\s+([A-Z0-9_]+|-1)\s*(?:;.*)?$")


def parse_pair_map(text: str, label: str) -> set[tuple[str, str]]:
    in_map = False
    pairs: set[tuple[str, str]] = set()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line == f"{label}:":
            in_map = True
            continue
        if not in_map:
            continue
        if not line or line.startswith(";"):
            continue
        if re.match(r"^\s*db\s+0\b", raw_line):
            return pairs
        match = PAIR_ENTRY_RE.match(raw_line)
        if not match:
            print(
                f"ERROR: malformed {label} entry: {raw_line}",
                file=sys.stderr,
            )
            raise SystemExit(1)
        pairs.add(match.groups())

    print(f"ERROR: could not locate terminated {label}.", file=sys.stderr)
    raise SystemExit(1)


def parse_class_list(text: str, label: str) -> list[str]:
    in_list = False
    classes: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line == f"{label}:":
            in_list = True
            continue
        if not in_list:
            continue
        if not line or line.startswith(";"):
            continue
        if line.endswith(":"):
            return classes
        match = CLASS_ENTRY_RE.match(raw_line)
        if not match:
            print(
                f"ERROR: malformed {label} entry: {raw_line}",
                file=sys.stderr,
            )
            raise SystemExit(1)
        value = match.group(1)
        if value == "-1":
            return classes
        classes.append(value)

    print(f"ERROR: could not locate terminated {label}.", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    if not AI_TIERS_FILE.exists():
        print(f"ERROR: missing file: {AI_TIERS_FILE}", file=sys.stderr)
        return 1
    if not LEADERS_FILE.exists():
        print(f"ERROR: missing file: {LEADERS_FILE}", file=sys.stderr)
        return 1
    if not MOVE_AI_FILE.exists():
        print(f"ERROR: missing file: {MOVE_AI_FILE}", file=sys.stderr)
        return 1
    if not BOSS_AI_FILE.exists():
        print(f"ERROR: missing file: {BOSS_AI_FILE}", file=sys.stderr)
        return 1
    if not TRAINER_ATTRIBUTES_FILE.exists():
        print(f"ERROR: missing file: {TRAINER_ATTRIBUTES_FILE}", file=sys.stderr)
        return 1

    ai_tiers_text = AI_TIERS_FILE.read_text(encoding="utf-8")
    leaders_text = LEADERS_FILE.read_text(encoding="utf-8")

    johto_leader_classes = {trainer_class for trainer_class, _trainer_id in JOHTO_LEADERS}
    kanto_leader_classes = {trainer_class for trainer_class, _trainer_id in KANTO_LEADERS}
    e4_champion_red_classes = {
        trainer_class
        for trainer_class, _trainer_id in ELITE_FOUR_AND_CHAMPION | POSTGAME_BOSSES
    }
    gym_leaders_table = set(parse_class_list(leaders_text, "GymLeaders"))
    kanto_gym_leaders_table = set(parse_class_list(leaders_text, "KantoGymLeaders"))

    missing_johto = sorted(johto_leader_classes - gym_leaders_table)
    missing_kanto = sorted(kanto_leader_classes - kanto_gym_leaders_table)
    unexpected_kanto = sorted(kanto_gym_leaders_table - kanto_leader_classes)
    allowed_gym_leaders = johto_leader_classes | e4_champion_red_classes
    unexpected_johto_table = sorted(gym_leaders_table - allowed_gym_leaders)
    if missing_johto or missing_kanto or unexpected_kanto or unexpected_johto_table:
        if missing_johto:
            print("ERROR: data/trainers/leaders.asm GymLeaders missing Johto leaders:", file=sys.stderr)
            for trainer_class in missing_johto:
                print(f"  - {trainer_class}", file=sys.stderr)
        if missing_kanto:
            print("ERROR: data/trainers/leaders.asm KantoGymLeaders missing Kanto leaders:", file=sys.stderr)
            for trainer_class in missing_kanto:
                print(f"  - {trainer_class}", file=sys.stderr)
        if unexpected_kanto:
            print("ERROR: unexpected KantoGymLeaders entries:", file=sys.stderr)
            for trainer_class in unexpected_kanto:
                print(f"  - {trainer_class}", file=sys.stderr)
        if unexpected_johto_table:
            print("ERROR: unexpected GymLeaders entries:", file=sys.stderr)
            for trainer_class in unexpected_johto_table:
                print(f"  - {trainer_class}", file=sys.stderr)
        return 1

    entries: dict[tuple[str, str], str] = {}
    in_tier_map = False
    for raw_line in ai_tiers_text.splitlines():
        line = raw_line.strip()
        if line == "BossAITierMap:":
            in_tier_map = True
            continue
        if not in_tier_map:
            continue
        if not line or line.startswith(";"):
            continue
        if re.match(r"^\s*db\s+0\b", raw_line):
            in_tier_map = False
            continue
        match = ENTRY_RE.match(raw_line)
        if not match:
            continue
        trainer_class, trainer_id, tier = match.groups()
        if trainer_class == "0":
            continue
        entries[(trainer_class, trainer_id)] = tier

    missing = sorted(TARGETS - set(entries))
    if missing:
        print("ERROR: missing required AI_TIER mappings:", file=sys.stderr)
        for trainer_class, trainer_id in missing:
            print(f"  - {trainer_class}, {trainer_id}", file=sys.stderr)
        return 1

    zero_or_unknown = sorted(
        (pair, tier)
        for pair, tier in entries.items()
        if pair in TARGETS and tier not in NONZERO_TIERS
    )
    if zero_or_unknown:
        print(
            "ERROR: required boss mappings must use non-zero tiers "
            "(AI_TIER_EARLY/MID/LATE):",
            file=sys.stderr,
        )
        for (trainer_class, trainer_id), tier in zero_or_unknown:
            print(f"  - {trainer_class}, {trainer_id} -> {tier}", file=sys.stderr)
        return 1

    adaptive_leads = parse_pair_map(ai_tiers_text, "AdaptiveLeadMap")
    missing_adaptive = sorted(ADAPTIVE_LEAD_TARGETS - adaptive_leads)
    extra_adaptive = sorted(adaptive_leads - ADAPTIVE_LEAD_TARGETS)
    if missing_adaptive or extra_adaptive:
        if missing_adaptive:
            print("ERROR: missing AdaptiveLeadMap entries:", file=sys.stderr)
            for trainer_class, trainer_id in missing_adaptive:
                print(f"  - {trainer_class}, {trainer_id}", file=sys.stderr)
        if extra_adaptive:
            print("ERROR: unexpected AdaptiveLeadMap entries:", file=sys.stderr)
            for trainer_class, trainer_id in extra_adaptive:
                print(f"  - {trainer_class}, {trainer_id}", file=sys.stderr)
        return 1

    boss_ai_text = BOSS_AI_FILE.read_text(encoding="utf-8")
    adaptive_match = re.search(
        r"\.ShouldUseAdaptiveLeadForTrainer:(?P<body>.*?)\.FindFirstAliveOTMon:",
        boss_ai_text,
        flags=re.DOTALL,
    )
    if not adaptive_match:
        print("ERROR: could not locate adaptive lead trainer gate.", file=sys.stderr)
        return 1
    adaptive_body = adaptive_match.group("body")
    if "AdaptiveLeadMap" not in adaptive_body:
        print("ERROR: adaptive lead gate must read AdaptiveLeadMap.", file=sys.stderr)
        return 1
    if "callfar IsGymLeader" in adaptive_body:
        print(
            "ERROR: adaptive lead policy must be table-driven, not IsGymLeader-driven.",
            file=sys.stderr,
        )
        return 1
    for trainer_class in ("FALKNER", "WHITNEY", "BUGSY", "MORTY", "RED"):
        if f"cp {trainer_class}" in adaptive_body:
            print(
                f"ERROR: adaptive lead gate still hard-codes {trainer_class}.",
                file=sys.stderr,
            )
            return 1

    move_ai_text = MOVE_AI_FILE.read_text(encoding="utf-8")
    if "Temporary safety path: Rival1" in move_ai_text:
        print(
            "ERROR: RIVAL1 move-choice bypass is still present; mapped rivals must use the normal boss AI path.",
            file=sys.stderr,
        )
        return 1

    attributes_text = TRAINER_ATTRIBUTES_FILE.read_text(encoding="utf-8")
    tier_loader_match = re.search(
        r"LoadBossAITier:(?P<body>.*?)ClearBossAIState:",
        attributes_text,
        flags=re.DOTALL,
    )
    if not tier_loader_match:
        print("ERROR: could not locate LoadBossAITier block.", file=sys.stderr)
        return 1
    tier_loader_body = tier_loader_match.group("body")
    if "cp RIVAL1" in tier_loader_body:
        print(
            "ERROR: LoadBossAITier contains a RIVAL1 special case; ai_tiers.asm mappings must not be nulled out.",
            file=sys.stderr,
        )
        return 1

    by_tier: dict[str, int] = {"AI_TIER_EARLY": 0, "AI_TIER_MID": 0, "AI_TIER_LATE": 0}
    for pair in TARGETS:
        tier = entries[pair]
        by_tier[tier] += 1

    print("AI_TIER mapping audit passed.")
    print(f"Required boss entries covered: {len(TARGETS)}")
    print(
        "Tier counts: "
        + ", ".join(f"{tier}={count}" for tier, count in by_tier.items())
    )
    print(f"Adaptive lead entries covered: {len(adaptive_leads)}")
    print("Mapped trainer class/id pairs:")
    for (trainer_class, trainer_id), tier in sorted(entries.items()):
        if (trainer_class, trainer_id) not in TARGETS:
            continue
        print(f"  - {trainer_class}, {trainer_id} -> {tier}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
