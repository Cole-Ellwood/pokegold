#!/usr/bin/env python3
"""Audit WRAMX bank 1 relief from linker outputs."""

from __future__ import annotations

import re
from pathlib import Path

from _common import fail, load


ROOT = Path(__file__).resolve().parents[2]
MAPS = (
    ("normal", ROOT / "pokegold.map", 29),
    ("trace", ROOT / "pokegold_trace.map", 2),
)
WRAMX_BANK_SIZE = 0x1000
MIN_FREE_BYTES = 410

BANK_RE = re.compile(r"^WRAMX bank #(?P<bank>\d+):$")
SECTION_RE = re.compile(
    r'^\tSECTION: \$[0-9a-fA-F]+-\$[0-9a-fA-F]+ '
    r'\(\$(?P<size>[0-9a-fA-F]+) bytes\) \["(?P<name>.+)"\]$'
)
LABEL_RE = re.compile(r"^\t\s+\$(?P<address>[0-9a-fA-F]+) = (?P<label>\S+)$")


def parse_wramx_bank1(map_text: str) -> tuple[int, dict[str, int]]:
    in_bank1 = False
    used = 0
    labels: dict[str, int] = {}

    for line in map_text.splitlines():
        bank_match = BANK_RE.match(line)
        if bank_match:
            in_bank1 = int(bank_match.group("bank")) == 1
            continue
        if in_bank1 and line and not line.startswith(("\t", " ")):
            in_bank1 = False
            continue
        if not in_bank1:
            continue

        section_match = SECTION_RE.match(line)
        if section_match:
            used += int(section_match.group("size"), 16)
            continue

        label_match = LABEL_RE.match(line)
        if label_match:
            labels[label_match.group("label")] = int(label_match.group("address"), 16)

    if used == 0:
        fail("could not parse any WRAMX bank 1 sections")
    return used, labels


def require_label(labels: dict[str, int], label: str, map_name: str) -> int:
    if label not in labels:
        fail(f"{map_name}: missing symbol in WRAMX bank 1 map: {label}")
    return labels[label]


def audit_map(name: str, path: Path, expected_boss_pad: int) -> tuple[int, int, int]:
    used, labels = parse_wramx_bank1(load(path))
    free = WRAMX_BANK_SIZE - used
    if free < MIN_FREE_BYTES:
        fail(
            f"{path.name}: WRAMX bank 1 has only {free} free bytes; "
            f"expected at least {MIN_FREE_BYTES}"
        )

    boss_start = require_label(labels, "wBossAITier", path.name)
    boss_end = require_label(labels, "wBossAIStateEnd", path.name)
    event_flags = require_label(labels, "wEventFlags", path.name)
    boss_pad = event_flags - boss_end
    if boss_pad != expected_boss_pad:
        fail(
            f"{path.name}: Boss AI reserve pad is {boss_pad} bytes; "
            f"expected {expected_boss_pad}"
        )
    if boss_end < boss_start:
        fail(f"{path.name}: Boss AI state end precedes start")

    print(
        f"{name}: WRAMX bank 1 used={used}, free={free}; "
        f"Boss AI live={boss_end - boss_start}, reserve_pad={boss_pad}"
    )
    return used, free, boss_pad


def main() -> int:
    for name, path, expected_boss_pad in MAPS:
        audit_map(name, path, expected_boss_pad)
    print("WRAMX bank 1 relief audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
