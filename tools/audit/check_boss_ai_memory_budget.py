#!/usr/bin/env python3
"""Audit Boss AI ROM/WRAM budget from linker outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
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

SAVE_ASM = ROOT / "engine" / "menus" / "save.asm"
MISC_CONSTANTS = ROOT / "constants" / "misc_constants.asm"
OFFSET_MAP_DATA = ROOT / "tools" / "audit" / "data" / "save_offset_map_fingerprints.json"

V2_OFF_RE = re.compile(r"^DEF\s+(V2_[A-Z0-9_]+_OFF)\s+EQU\s+\$([0-9a-fA-F]+)")
V2_SIZE_RE = re.compile(r"^DEF\s+(V2_[A-Z0-9_]+_SIZE)\s+EQU\s+\$([0-9a-fA-F]+)")
CHUNK_RE = re.compile(
    r"^\s*copy_v2_save_chunk\s+\\1,\s*(V2_[A-Z0-9_]+_OFF),\s*"
    r"([A-Za-z0-9_]+(?:\s*\+\s*\d+)?),\s*"
    r"([A-Za-z0-9_]+(?:\s*\+\s*\d+)?)\s*(?:;.*)?$"
)
SAVE_VERSION_RE = re.compile(r"^\s*DEF\s+SAVE_FORMAT_VERSION\s+EQU\s+(\d+)")


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


def parse_v2_constants() -> tuple[dict[str, int], dict[str, int]]:
    offsets: dict[str, int] = {}
    sizes: dict[str, int] = {}
    for line in load(SAVE_ASM).splitlines():
        off_match = V2_OFF_RE.match(line)
        if off_match:
            offsets[off_match.group(1)] = int(off_match.group(2), 16)
            continue
        size_match = V2_SIZE_RE.match(line)
        if size_match:
            sizes[size_match.group(1)] = int(size_match.group(2), 16)
    if not offsets:
        fail("save.asm: no V2_*_OFF constants found")
    return offsets, sizes


def parse_chunks() -> list[tuple[str, str, str]]:
    chunks: list[tuple[str, str, str]] = []
    for line in load(SAVE_ASM).splitlines():
        match = CHUNK_RE.match(line)
        if match:
            chunks.append((match.group(1), match.group(2), match.group(3)))
    if not chunks:
        fail("save.asm: no copy_v2_save_chunk lines found")
    return chunks


def parse_save_format_version() -> int:
    for line in load(MISC_CONSTANTS).splitlines():
        match = SAVE_VERSION_RE.match(line)
        if match:
            return int(match.group(1))
    fail(f"could not parse SAVE_FORMAT_VERSION from {MISC_CONSTANTS.relative_to(ROOT)}")
    return 0


def resolve_label_addr(token: str, symbols: dict[str, tuple[int, int]]) -> int:
    token = token.strip()
    if "+" in token:
        base, _, offset_text = token.partition("+")
        base = base.strip()
        extra = int(offset_text.strip())
    else:
        base, extra = token, 0
    bank, addr = require_symbol(symbols, base)
    if bank != 1:
        fail(f"save.asm chunk symbol {base} is not in WRAM bank 1")
    return addr + extra


def audit_save_offset_map(symbols: dict[str, tuple[int, int]], update: bool) -> None:
    """Verify the v2 save image is overlap-free and its per-field byte offsets
    have not drifted without a SAVE_FORMAT_VERSION bump.

    check_save_format_version.py fingerprints saved WRAM by label only and
    cannot see `ds N` size tweaks (it says so). This closes that gap: it walks
    the actual linked addresses (pokegold.sym) through the v2 chunk offset map
    and fingerprints every saved field's absolute file offset. The wBossAI*
    reserve block is excluded because the fixed 140-byte pad keeps everything
    after it pinned regardless of internal wBossAI* churn.
    """
    offsets, sizes = parse_v2_constants()
    chunks = parse_chunks()

    resolved: list[tuple[str, int, int, int]] = []  # (offset_name, offset, start_addr, size)
    for off_name, start_token, end_token in chunks:
        if off_name not in offsets:
            fail(f"save.asm chunk uses undefined offset constant {off_name}")
        start_addr = resolve_label_addr(start_token, symbols)
        end_addr = resolve_label_addr(end_token, symbols)
        if end_addr < start_addr:
            fail(f"save.asm chunk {off_name}: end {end_token} precedes start {start_token}")
        resolved.append((off_name, offsets[off_name], start_addr, end_addr - start_addr))

    # Hard check: no chunk may run into the next one's pinned offset.
    ordered = sorted(resolved, key=lambda row: row[1])
    for (a_name, a_off, _, a_size), (b_name, b_off, _, _) in zip(ordered, ordered[1:]):
        if a_off + a_size > b_off:
            fail(
                f"v2 save chunks overlap: {a_name} (${a_off:04x}+{a_size}) runs into "
                f"{b_name} (${b_off:04x}); a chunk grew past its pinned slot and old "
                "saves would corrupt"
            )

    game_size = sizes.get("V2_GAME_DATA_SIZE")
    if game_size is not None:
        last_name, last_off, _, last_size = ordered[-1]
        if last_off + last_size > game_size:
            fail(f"v2 save: chunk {last_name} exceeds V2_GAME_DATA_SIZE (${game_size:04x})")

    offset_map: dict[str, int] = {}
    for name, (bank, addr) in symbols.items():
        if bank != 1 or not name.startswith("w") or name.startswith("wBossAI"):
            continue
        for _, off, start_addr, size in resolved:
            if start_addr <= addr < start_addr + size:
                offset_map[name] = off + (addr - start_addr)
                break

    canonical = json.dumps(offset_map, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    version = parse_save_format_version()
    key = str(version)
    stored = (
        json.loads(OFFSET_MAP_DATA.read_text(encoding="utf-8"))
        if OFFSET_MAP_DATA.exists()
        else {}
    )

    if update:
        stored[key] = digest
        OFFSET_MAP_DATA.parent.mkdir(parents=True, exist_ok=True)
        OFFSET_MAP_DATA.write_text(
            json.dumps(stored, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"Recorded save offset map for SAVE_FORMAT_VERSION={version}: {digest}")
        return

    expected = stored.get(key)
    if expected is None:
        fail(
            f"no save offset map fingerprint for SAVE_FORMAT_VERSION={version}; "
            "run check_boss_ai_memory_budget.py --update if this is intentional"
        )
    if expected != digest:
        print(f"current save offset map:  {digest}")
        print(f"expected save offset map: {expected}")
        fail(
            "saved-field byte offsets changed without a SAVE_FORMAT_VERSION bump. "
            "A ds-size tweak or V2_*_OFF change moved a field in the save image, so "
            "old saves would misalign. Revert it, or bump SAVE_FORMAT_VERSION and run "
            "check_boss_ai_memory_budget.py --update."
        )
    print(f"Save offset map matches SAVE_FORMAT_VERSION={version} ({len(offset_map)} fields).")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit Boss AI ROM/WRAM budget and the v2 save offset map."
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help=(
            "rebaseline the save offset map fingerprint for the current "
            "SAVE_FORMAT_VERSION. Use only after a deliberate version bump."
        ),
    )
    args = parser.parse_args(argv)

    normal_enemy, normal_core = audit_map(NORMAL_MAP, trace=False)
    trace_enemy, _ = audit_map(TRACE_MAP, trace=True)
    normal_wram = audit_symbols(NORMAL_SYM, trace=False)
    trace_wram = audit_symbols(TRACE_SYM, trace=True)
    audit_dev_index(normal_enemy, normal_core, normal_wram, trace_wram)
    audit_save_offset_map(parse_symbols(load(NORMAL_SYM)), update=args.update)

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
