"""Read-only WRAMX bank 1 audit helper for the 2026-05-24 relief plan."""

from __future__ import annotations

import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAPS = ["pokegold.map", "pokegold_trace.map"]
RAM = ROOT / "ram" / "wram.asm"
EVENTS = ROOT / "constants" / "event_flags.asm"

SECTION_RE = re.compile(
    r'^\s*SECTION:\s+\$([0-9a-f]{4})-\$([0-9a-f]{4})\s+\(\$([0-9a-f]{4}) bytes\)\s+\["([^"]+)"\]',
    re.IGNORECASE,
)
BANK_RE = re.compile(r"^WRAMX bank #(\d+):")
LABEL_RE = re.compile(r"^\s*\$([0-9a-f]{4}) = ([A-Za-z_][A-Za-z0-9_.$]*)", re.IGNORECASE)


def parse_wramx_map(map_name: str) -> dict[int, list[dict[str, object]]]:
    banks: dict[int, list[dict[str, object]]] = {}
    current_bank: int | None = None
    current_section: dict[str, object] | None = None
    for line in (ROOT / map_name).read_text(encoding="utf-8", errors="replace").splitlines():
        bank_match = BANK_RE.match(line)
        if bank_match:
            current_bank = int(bank_match.group(1))
            banks.setdefault(current_bank, [])
            current_section = None
            continue
        if current_bank is None:
            continue
        if line and not line.startswith(("\t", " ")):
            current_bank = None
            current_section = None
            continue
        section_match = SECTION_RE.match(line)
        if section_match:
            start = int(section_match.group(1), 16)
            end = int(section_match.group(2), 16)
            size = int(section_match.group(3), 16)
            current_section = {
                "name": section_match.group(4),
                "start": start,
                "end": end,
                "size": size,
                "labels": [],
            }
            banks[current_bank].append(current_section)
            continue
        label_match = LABEL_RE.match(line)
        if label_match and current_section is not None:
            current_section["labels"].append(
                (int(label_match.group(1), 16), label_match.group(2))
            )
    return banks


def label_addresses(map_name: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for sections in parse_wramx_map(map_name).values():
        for section in sections:
            for addr, label in section["labels"]:
                out.setdefault(label, addr)
    return out


def event_constant_stats() -> dict[str, int]:
    current = 0
    real_events = 0
    skips = 0
    jumps: list[tuple[int, int]] = []
    highest_real = -1
    for raw in EVENTS.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        if line == "const_def":
            current = 0
            continue
        if line.startswith("const_next"):
            new_value = int(line.split()[1], 0)
            jumps.append((current, new_value))
            current = new_value
            continue
        if line.startswith("const_skip"):
            parts = line.split()
            count = int(parts[1], 0) if len(parts) > 1 else 1
            skips += count
            current += count
            continue
        if line.startswith("const EVENT_"):
            real_events += 1
            highest_real = max(highest_real, current)
            current += 1
            continue
        if line.startswith("DEF NUM_EVENTS"):
            break
    return {
        "current_num_events": current,
        "current_bytes": math.ceil(current / 8),
        "real_events": real_events,
        "skips": skips,
        "highest_real_event": highest_real,
        "highest_real_bytes": math.ceil((highest_real + 1) / 8),
        "packed_bytes": math.ceil(real_events / 8),
        "jump_gap_bytes_if_packed": math.ceil(current / 8) - math.ceil(real_events / 8),
        "highest_gap_bytes": math.ceil(current / 8) - math.ceil((highest_real + 1) / 8),
        "jumps": jumps,
    }


KEY_LABELS = [
    "wTempMon",
    "wTrainerBattleContextBackup",
    "wUsedSprites",
    "wMapPartial",
    "wMapAttributes",
    "wTileset",
    "wEnemyAIMoveScores",
    "wSwitchMonBuffer",
    "wPlayerData1",
    "wObjectStructs",
    "wCmdQueue",
    "wMapObjects",
    "wVariableSprites",
    "wPlayerData3",
    "wTMsHMs",
    "wItems",
    "wKeyItems",
    "wBalls",
    "wPCItems",
    "wTradeFlags",
    "wTMTutorTMHMBackup",
    "wBossAITier",
    "wBossAIStateEnd",
    "wEventFlags",
    "wBoxNames",
    "wFruitTreeFlags",
    "wPhoneList",
    "wPlayerData3End",
    "wPokemonData",
    "wPartyMons",
    "wPartyMonOTs",
    "wPartyMonNicknames",
    "wPokedexCaught",
    "wPokedexSeen",
    "wUnownDex",
    "wBreedMon1Nickname",
    "wBreedMon2Nickname",
    "wEggMonNickname",
    "wContestMon",
    "wRoamMon1",
    "wMagikarpRecordHoldersName",
    "wOTPartyData",
    "wOTPartyMons",
    "wPokemonDataEnd",
    "wStackBottom",
    "wStackTop",
]


def size_between(addrs: dict[str, int], start_label: str, end_label: str) -> int:
    return addrs[end_label] - addrs[start_label]


def main() -> None:
    for map_name in MAPS:
        print(f"== {map_name} ==")
        banks = parse_wramx_map(map_name)
        for bank in sorted(banks):
            print(f"WRAMX bank {bank}:")
            total = 0
            for section in banks[bank]:
                total += int(section["size"])
                print(
                    f"  {section['name']}: "
                    f"${section['start']:04x}-${section['end']:04x} "
                    f"{section['size']} bytes"
                )
            print(f"  section total: {total} bytes")
        addrs = label_addresses(map_name)
        print("  Boss AI reserve:")
        for label in (
            "wBossAITier",
            "wBossAIStateEnd",
            "wEventFlags",
            "wBossAITraceTopMoves",
        ):
            if label in addrs:
                print(f"    {label}: ${addrs[label]:04x}")
        if "wBossAITier" in addrs and "wBossAIStateEnd" in addrs:
            print(
                "    live boss bytes: "
                f"{size_between(addrs, 'wBossAITier', 'wBossAIStateEnd')}"
            )
        if "wBossAIStateEnd" in addrs and "wEventFlags" in addrs:
            print(
                "    reserve pad bytes: "
                f"{size_between(addrs, 'wBossAIStateEnd', 'wEventFlags')}"
            )
        print("  selected label sizes:")
        sorted_addrs = sorted((addr, label) for label, addr in addrs.items())
        by_label = {label: i for i, (addr, label) in enumerate(sorted_addrs)}
        for label in KEY_LABELS:
            if label not in by_label:
                continue
            i = by_label[label]
            addr = sorted_addrs[i][0]
            next_addr = None
            for j in range(i + 1, len(sorted_addrs)):
                if sorted_addrs[j][0] > addr:
                    next_addr = sorted_addrs[j][0]
                    break
            if next_addr is None:
                continue
            print(f"    {label}: ${addr:04x} size_to_next {next_addr - addr}")
    stats = event_constant_stats()
    print("== event flag constants ==")
    for key, value in stats.items():
        if key == "jumps":
            print(f"{key}: {value}")
        else:
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
