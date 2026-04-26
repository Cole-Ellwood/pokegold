#!/usr/bin/env python3
"""Audit Boss AI ROM/WRAM budget from linker outputs."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
NORMAL_MAP = ROOT / "pokegold.map"
NORMAL_SYM = ROOT / "pokegold.sym"
TRACE_MAP = ROOT / "pokegold_trace.map"
TRACE_SYM = ROOT / "pokegold_trace.sym"
DEV_INDEX = ROOT / "docs" / "generated" / "dev_index.md"

SECTION_RE = re.compile(
    r'^\tSECTION: \$(?P<start>[0-9a-fA-F]+)-\$(?P<end>[0-9a-fA-F]+) '
    r'\(\$(?P<size>[0-9a-fA-F]+) bytes\) \["(?P<name>.+)"\]$'
)
BANK_RE = re.compile(r"^(?P<memory>[A-Z0-9]+) bank #(?P<bank>\d+):$")
LABEL_RE = re.compile(r"^\t\s+\$(?P<address>[0-9a-fA-F]+) = (?P<name>\S+)$")
SYM_RE = re.compile(r"^(?P<bank>[0-9a-fA-F]{2}):(?P<address>[0-9a-fA-F]{4}) (?P<name>\S+)$")

BOSS_RESERVE_BYTES = 140


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def load(path: Path) -> str:
    if not path.exists():
        fail(f"missing required file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8", errors="replace")


def parse_sections(map_text: str) -> list[dict[str, object]]:
    sections: list[dict[str, object]] = []
    current_memory = ""
    current_bank = -1
    current_section: dict[str, object] | None = None

    for line in map_text.splitlines():
        bank_match = BANK_RE.match(line)
        if bank_match:
            current_memory = bank_match.group("memory")
            current_bank = int(bank_match.group("bank"))
            current_section = None
            continue

        section_match = SECTION_RE.match(line)
        if section_match:
            current_section = {
                "memory": current_memory,
                "bank": current_bank,
                "start": int(section_match.group("start"), 16),
                "end": int(section_match.group("end"), 16),
                "size": int(section_match.group("size"), 16),
                "name": section_match.group("name"),
                "labels": [],
            }
            sections.append(current_section)
            continue

        label_match = LABEL_RE.match(line)
        if label_match and current_section is not None:
            labels = current_section["labels"]
            assert isinstance(labels, list)
            labels.append(label_match.group("name"))

    return sections


def find_section(sections: list[dict[str, object]], name: str) -> dict[str, object]:
    matches = [section for section in sections if section["name"] == name]
    if not matches:
        fail(f"missing map section: {name}")
    if len(matches) > 1:
        fail(f"multiple map sections named {name}")
    return matches[0]


def parse_symbols(sym_text: str) -> dict[str, tuple[int, int]]:
    out: dict[str, tuple[int, int]] = {}
    for line in sym_text.splitlines():
        match = SYM_RE.match(line)
        if not match:
            continue
        out[match.group("name")] = (
            int(match.group("bank"), 16),
            int(match.group("address"), 16),
        )
    return out


def require_symbol(symbols: dict[str, tuple[int, int]], name: str) -> tuple[int, int]:
    if name not in symbols:
        fail(f"missing symbol: {name}")
    return symbols[name]


def audit_map(path: Path, trace: bool) -> tuple[dict[str, object], dict[str, object]]:
    sections = parse_sections(load(path))
    enemy = find_section(sections, "Enemy Trainers")
    core = find_section(sections, "Battle Core")

    if enemy["memory"] != "ROMX":
        fail(f"{path.name}: Enemy Trainers is not ROMX")
    if int(enemy["bank"]) != 0x0E:
        fail(f"{path.name}: Enemy Trainers bank changed")
    if int(enemy["end"]) >= 0x8000:
        fail(f"{path.name}: Enemy Trainers overflows ROMX bank")

    if core["memory"] != "ROMX":
        fail(f"{path.name}: Battle Core is not ROMX")
    if int(core["bank"]) != 0x0F:
        fail(f"{path.name}: Battle Core bank changed")
    if int(core["start"]) != 0x4000:
        fail(f"{path.name}: Battle Core range changed")
    if int(core["end"]) >= 0x8000:
        fail(f"{path.name}: Battle Core overflows ROMX bank")
    if int(core["size"]) > 0x4000:
        fail(f"{path.name}: Battle Core size exceeds ROMX bank")

    labels = core["labels"]
    assert isinstance(labels, list)
    boss_labels = [label for label in labels if str(label).startswith("BossAI_")]
    if boss_labels:
        fail(f"{path.name}: Battle Core contains BossAI labels: {boss_labels[:5]}")

    if trace and int(enemy["end"]) < 0x7000:
        fail(f"{path.name}: trace Enemy Trainers section did not include trace growth")

    return enemy, core


def audit_symbols(path: Path, trace: bool) -> tuple[int, int, int]:
    symbols = parse_symbols(load(path))
    tier_bank, tier = require_symbol(symbols, "wBossAITier")
    end_bank, state_end = require_symbol(symbols, "wBossAIStateEnd")
    event_bank, event_flags = require_symbol(symbols, "wEventFlags")

    if tier_bank != 1 or end_bank != 1 or event_bank != 1:
        fail(f"{path.name}: Boss AI WRAM symbols must stay in WRAMX bank 1")
    if state_end > event_flags:
        fail(f"{path.name}: wBossAIStateEnd overlaps wEventFlags")
    if event_flags - tier > BOSS_RESERVE_BYTES:
        fail(f"{path.name}: Boss AI reserve exceeds {BOSS_RESERVE_BYTES} bytes")

    if trace:
        require_symbol(symbols, "wBossAITraceTopMoves")
        require_symbol(symbols, "wBossAITraceRiskFlags")
    else:
        if "wBossAITraceTopMoves" in symbols:
            fail(f"{path.name}: normal build unexpectedly has trace fields")

    return tier, state_end, event_flags


def audit_dev_index(
    normal_enemy: dict[str, object],
    normal_core: dict[str, object],
    normal_wram: tuple[int, int, int],
    trace_wram: tuple[int, int, int],
) -> None:
    text = load(DEV_INDEX)
    tier, state_end, event_flags = normal_wram
    trace_tier, trace_end, trace_event_flags = trace_wram

    if tier != trace_tier or event_flags != trace_event_flags:
        fail("normal and trace Boss AI reserve anchors differ unexpectedly")

    normal_used = state_end - tier
    trace_used = trace_end - trace_tier
    normal_free = event_flags - state_end
    trace_free = trace_event_flags - trace_end

    expected_rows = (
        f"| Normal | {normal_used} | {normal_free} |",
        f"| With `BOSS_AI_TRACE` fields | {trace_used} | {trace_free} |",
        f"| `wBossAITier` | 01:{tier:04x} | Boss AI state start |",
        f"| `wBossAIStateEnd` | 01:{state_end:04x} | Logical end before reserve padding |",
        f"| `wEventFlags` | 01:{event_flags:04x} | First unrelated field after reserved block |",
        f"| `Enemy Trainers` | ROMX | 0e:4000-{int(normal_enemy['end']):04x} | {int(normal_enemy['size'])} |",
        f"| `Battle Core` | ROMX | 0f:4000-{int(normal_core['end']):04x} | {int(normal_core['size'])} |",
    )

    missing = [row for row in expected_rows if row not in text]
    if missing:
        print("Generated dev index does not match Boss AI linker budget rows:")
        for row in missing:
            print(f"  expected substring: {row}")
        fail("regenerate docs/generated/dev_index.md")


def main() -> int:
    normal_enemy, normal_core = audit_map(NORMAL_MAP, trace=False)
    trace_enemy, _ = audit_map(TRACE_MAP, trace=True)
    normal_wram = audit_symbols(NORMAL_SYM, trace=False)
    trace_wram = audit_symbols(TRACE_SYM, trace=True)
    audit_dev_index(normal_enemy, normal_core, normal_wram, trace_wram)

    print("Boss AI memory budget audit passed.")
    print(
        "Enemy Trainers:"
        f" normal=0e:4000-{int(normal_enemy['end']):04x},"
        f" trace=0e:4000-{int(trace_enemy['end']):04x}"
    )
    print(
        "Boss AI WRAM:"
        f" normal_used={normal_wram[1] - normal_wram[0]},"
        f" normal_free={normal_wram[2] - normal_wram[1]},"
        f" trace_used={trace_wram[1] - trace_wram[0]},"
        f" trace_free={trace_wram[2] - trace_wram[1]}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
