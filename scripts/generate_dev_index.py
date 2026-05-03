#!/usr/bin/env python3
"""Generate a developer navigation index from RGBDS linker outputs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
import argparse
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {
    ".claude",
    ".git",
    ".local",
    "__pycache__",
    "dist",
    "outbox",
    "rgbds-1.0.1",
    "workspace",
}

SUMMARY_RE = re.compile(
    r"^\t(?P<memory>[A-Z0-9]+): (?P<used>\d+) bytes used / "
    r"(?P<free>\d+) free(?: in (?P<banks>\d+) banks)?"
)
BANK_RE = re.compile(r"^(?P<memory>[A-Z0-9]+) bank #(?P<bank>\d+):$")
SECTION_RE = re.compile(
    r'^\tSECTION: \$(?P<start>[0-9a-fA-F]+)'
    r'(?:-\$(?P<end>[0-9a-fA-F]+))? '
    r'\(\$(?P<size>[0-9a-fA-F]+) bytes?\) \["(?P<name>.+)"\]$'
)
EMPTY_RANGE_RE = re.compile(
    r"^\tEMPTY: \$(?P<start>[0-9a-fA-F]+)-\$(?P<end>[0-9a-fA-F]+) "
    r"\(\$(?P<size>[0-9a-fA-F]+) bytes?\)$"
)
LABEL_IN_MAP_RE = re.compile(r"^\t\s+\$(?P<address>[0-9a-fA-F]+) = (?P<name>\S+)$")
SYM_RE = re.compile(r"^(?P<bank>[0-9a-fA-F]{2}):(?P<address>[0-9a-fA-F]{4}) (?P<name>\S+)$")
ASM_SECTION_RE = re.compile(r'^\s*SECTION\s+"(?P<name>[^"]+)"')
ASM_INCLUDE_RE = re.compile(r'^\s*INCLUDE\s+"(?P<path>[^"]+)"')
ASM_LABEL_RE = re.compile(r"^\s*(?P<name>[A-Za-z_.$][A-Za-z0-9_.$]*)\s*:{1,2}")
LAYOUT_ROMX_RE = re.compile(r"^ROMX(?: \$(?P<bank>[0-9a-fA-F]+))?")
LAYOUT_SECTION_RE = re.compile(r'^\s*"(?P<name>[^"]+)"')


@dataclass(frozen=True)
class SummaryRow:
    memory: str
    used: int
    free: int
    banks: int | None = None


@dataclass
class SectionEntry:
    memory: str
    bank: int
    start: int
    end: int
    size: int
    name: str
    labels: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class EmptyRange:
    memory: str
    bank: int
    start: int
    end: int
    size: int


@dataclass(frozen=True)
class Symbol:
    bank: int
    address: int
    name: str


@dataclass(frozen=True)
class SourceLoc:
    path: str
    line: int


@dataclass(frozen=True)
class Area:
    title: str
    intent: str
    paths: tuple[str, ...]
    symbols: tuple[str, ...]


AREAS: tuple[Area, ...] = (
    Area(
        title="Developer docs and review workflow",
        intent="Project intent, review order, bug-hunt checklist, and generated lookup.",
        paths=(
            "docs/README.md",
            "docs/project_context.md",
            "docs/review_playbook.md",
            "docs/project_map.md",
            "docs/boss_ai_spec.md",
            "docs/generated/dev_index.md",
            "scripts/generate_dev_index.py",
        ),
        symbols=(),
    ),
    Area(
        title="Boss AI and trainer difficulty",
        intent="Human-like major fights, no hidden-information cheating outside authored Haki.",
        paths=(
            "engine/battle/ai/boss.asm",
            "engine/battle/ai/move.asm",
            "engine/battle/ai/scoring.asm",
            "engine/battle/ai/items.asm",
            "engine/battle/ai/switch.asm",
            "engine/battle/core.asm",
            "engine/battle/used_move_text.asm",
            "engine/battle/read_trainer_attributes.asm",
            "data/trainers/ai_tiers.asm",
            "data/trainers/parties.asm",
            "data/trainers/attributes.asm",
            "constants/battle_constants.asm",
        ),
        symbols=(
            "BossAI_IncrementTurnsElapsed",
            "BossAI_RecordPlayerSwitch",
            "BossAI_SelectMove",
            "BossAI_SwitchOrTryItem",
            "BossAI_ComputeSwitchConfidence",
            "BossAI_PredictPlayerSwitch",
            "BossAI_RecordRevealedPlayerMove",
            "BossAI_CurrentEnemyMoveHasKOPressure",
            "BossAI_CurrentEnemyMovePressureScore",
            "BossAI_PlayerHasPublicThreatVsEnemy",
            "BossAI_PublicEnemyFaster",
            "BossAI_CheckAbleToSwitchSafe",
            "BossAI_RefineSwitchCandidateForPlausibleRisk",
            "BossAI_ApplyPlausibleRiskToSwitchConfidence",
            "BossAITierMap",
            "CheckPlayerMoveTypeMatchups",
            "AICompareSpeed",
            "AIDamageCalc",
        ),
    ),
    Area(
        title="Battle mechanics",
        intent="Shared damage, status, switching, item, and turn-flow rules.",
        paths=(
            "engine/battle/core.asm",
            "engine/battle/effect_commands.asm",
            "engine/battle/type_passive_damage_mods.asm",
            "engine/battle/late_gen_held_items.asm",
            "engine/battle/move_effects",
            "constants/battle_constants.asm",
        ),
        symbols=(
            "TypePassive_ApplyDamageModifiers_Far",
            "TypePassive_TryDarkStatusShield_Far",
            "TypePassive_MaybePoisonRetaliation_Far",
            "ApplyLateGenDamageMultipliers_Far",
            "HandleLateGenAfterHitEffects_Far",
            "TryActivateDittoImposter",
        ),
    ),
    Area(
        title="Moves",
        intent="Move stats, effects, descriptions, contact flags, and animations.",
        paths=(
            "data/moves/moves.asm",
            "data/moves/effects.asm",
            "data/moves/effects_pointers.asm",
            "data/moves/contact_flags.asm",
            "data/moves/descriptions.asm",
            "constants/move_constants.asm",
        ),
        symbols=("Moves", "MoveEffects", "MoveContactFlags", "Spikes", "RapidSpin"),
    ),
    Area(
        title="Items and held items",
        intent="Item data, descriptions, pockets, marts, and battle held effects.",
        paths=(
            "data/items/attributes.asm",
            "data/items/descriptions.asm",
            "data/items/names.asm",
            "data/items/marts.asm",
            "engine/items",
            "engine/battle/late_gen_held_items.asm",
        ),
        symbols=(
            "ItemAttributes",
            "ItemDescriptions",
            "ItemNames",
            "IsChoiceHeldEffect_Far",
            "IsMoveBlockedByAssaultVest_Far",
        ),
    ),
    Area(
        title="Pokemon data and weak-Pokemon buffs",
        intent="Base stats, types, level-up moves, evolutions, egg moves, and names.",
        paths=(
            "data/pokemon/base_stats.asm",
            "data/pokemon/base_stats",
            "data/pokemon/evos_attacks.asm",
            "data/pokemon/evos_attacks_pointers.asm",
            "data/pokemon/egg_moves.asm",
            "constants/pokemon_constants.asm",
        ),
        symbols=("BaseData", "EvosAttacks", "EvosAttacksPointers", "EggMovePointers"),
    ),
    Area(
        title="Maps, events, and QoL scripts",
        intent="Map scripts, specials, NPC events, progression, tutors, and reminders.",
        paths=(
            "maps",
            "data/maps",
            "data/events/special_pointers.asm",
            "engine/events/move_reminder.asm",
            "engine/events/tm_tutor.asm",
            "engine/overworld",
        ),
        symbols=("Special", "SpecialsPointers", "MoveReminder", "TMTutorTeachAnyTM"),
    ),
    Area(
        title="RAM, saves, and temporary battle state",
        intent="WRAM, SRAM, VRAM, HRAM, save data, and low-memory pressure points.",
        paths=("ram/wram.asm", "ram/sram.asm", "ram/vram.asm", "ram/hram.asm"),
        symbols=("wBattleMode", "wPlayerMon", "wEnemyMon", "wBattleMon", "hROMBank"),
    ),
    Area(
        title="Graphics",
        intent="Pokemon pics, trainer pics, sprites, tilesets, palettes, and UI art.",
        paths=("gfx", "data/sprites", "data/tilesets.asm", "gfx/pics_gold.asm"),
        symbols=("PokemonPicPointers", "TrainerPicPointers", "Tilesets"),
    ),
    Area(
        title="Audio",
        intent="Music, cries, sound effects, engine data, and song banks.",
        paths=("audio", "audio.asm", "constants/music_constants.asm", "constants/sfx_constants.asm"),
        symbols=("Music", "SFX", "Cries", "MusicPointers", "SFXPointers"),
    ),
)

NOTABLE_SECTIONS = (
    "Home",
    "bankB",
    "Enemy Trainers",
    "Late Gen Held Items",
    "Effect Commands",
    "Battle Core",
    "Evolutions and Attacks",
    "Maps",
    "Events",
    "Standard Scripts",
    "Phone Scripts",
    "Map Scripts",
    "Audio",
    "Sound Effects",
    "Cries",
)

BOSS_AI_RESERVED_BYTES = 140


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def hex4(value: int) -> str:
    return f"${value:04x}"


def bank_addr(bank: int, address: int) -> str:
    return f"{bank:02x}:{address:04x}"


def bank_range(entry: SectionEntry | EmptyRange) -> str:
    return f"{entry.bank:02x}:{entry.start:04x}-{entry.end:04x}"


def full_empty_range(memory: str) -> tuple[int, int, int] | None:
    if memory == "ROM0":
        return (0x0000, 0x3FFF, 0x4000)
    if memory == "ROMX":
        return (0x4000, 0x7FFF, 0x4000)
    if memory == "VRAM":
        return (0x8000, 0x9FFF, 0x2000)
    if memory == "SRAM":
        return (0xA000, 0xBFFF, 0x2000)
    if memory == "WRAM0":
        return (0xC000, 0xCFFF, 0x1000)
    if memory == "WRAMX":
        return (0xD000, 0xDFFF, 0x1000)
    if memory == "HRAM":
        return (0xFF80, 0xFFFE, 0x007F)
    return None


def iter_asm_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*.asm"):
        if any(part in EXCLUDED_DIRS for part in path.relative_to(ROOT).parts):
            continue
        files.append(path)
    return sorted(files, key=rel)


def parse_map(path: Path) -> tuple[list[SummaryRow], list[SectionEntry], list[EmptyRange]]:
    summary: list[SummaryRow] = []
    sections: list[SectionEntry] = []
    empties: list[EmptyRange] = []
    current_memory = ""
    current_bank = 0
    current_section: SectionEntry | None = None

    for line in path.read_text(encoding="utf-8").splitlines():
        summary_match = SUMMARY_RE.match(line)
        if summary_match:
            summary.append(
                SummaryRow(
                    memory=summary_match.group("memory"),
                    used=int(summary_match.group("used")),
                    free=int(summary_match.group("free")),
                    banks=(
                        int(summary_match.group("banks"))
                        if summary_match.group("banks") is not None
                        else None
                    ),
                )
            )
            continue

        bank_match = BANK_RE.match(line)
        if bank_match:
            current_memory = bank_match.group("memory")
            current_bank = int(bank_match.group("bank"))
            current_section = None
            continue

        section_match = SECTION_RE.match(line)
        if section_match:
            start = int(section_match.group("start"), 16)
            size = int(section_match.group("size"), 16)
            end = (
                int(section_match.group("end"), 16)
                if section_match.group("end") is not None
                else start + max(size - 1, 0)
            )
            current_section = SectionEntry(
                memory=current_memory,
                bank=current_bank,
                start=start,
                end=end,
                size=size,
                name=section_match.group("name"),
            )
            sections.append(current_section)
            continue

        empty_match = EMPTY_RANGE_RE.match(line)
        if empty_match:
            empties.append(
                EmptyRange(
                    memory=current_memory,
                    bank=current_bank,
                    start=int(empty_match.group("start"), 16),
                    end=int(empty_match.group("end"), 16),
                    size=int(empty_match.group("size"), 16),
                )
            )
            current_section = None
            continue

        if line == "\tEMPTY":
            full_range = full_empty_range(current_memory)
            if full_range is not None:
                start, end, size = full_range
                empties.append(
                    EmptyRange(
                        memory=current_memory,
                        bank=current_bank,
                        start=start,
                        end=end,
                        size=size,
                    )
                )
            current_section = None
            continue

        label_match = LABEL_IN_MAP_RE.match(line)
        if label_match and current_section is not None:
            current_section.labels.append(label_match.group("name"))

    return summary, sections, empties


def parse_sym(path: Path) -> dict[str, Symbol]:
    symbols: dict[str, Symbol] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = SYM_RE.match(line)
        if not match:
            continue
        name = match.group("name")
        symbols.setdefault(
            name,
            Symbol(
                bank=int(match.group("bank"), 16),
                address=int(match.group("address"), 16),
                name=name,
            ),
        )
    return symbols


def parse_layout(path: Path) -> dict[str, tuple[str, int | None]]:
    layout: dict[str, tuple[str, int | None]] = {}
    current_memory: str | None = None
    current_bank: int | None = None

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped == "ROM0":
            current_memory = "ROM0"
            current_bank = 0
            continue
        romx_match = LAYOUT_ROMX_RE.match(stripped)
        if romx_match:
            current_memory = "ROMX"
            current_bank = (
                int(romx_match.group("bank"), 16)
                if romx_match.group("bank") is not None
                else None
            )
            continue
        if stripped.startswith(("SRAM", "WRAM", "VRAM", "HRAM")):
            current_memory = stripped.split()[0]
            current_bank = None
            continue

        section_match = LAYOUT_SECTION_RE.match(line)
        if section_match and current_memory is not None:
            layout[section_match.group("name")] = (current_memory, current_bank)

    return layout


def parse_source_indexes(
    asm_files: list[Path],
) -> tuple[dict[str, list[SourceLoc]], dict[str, set[str]]]:
    label_sources: dict[str, list[SourceLoc]] = {}
    section_sources: dict[str, set[str]] = {}

    for path in asm_files:
        current_global: str | None = None
        current_section: str | None = None
        rel_path = rel(path)

        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            lines = path.read_text(encoding="latin-1").splitlines()

        for line_number, raw_line in enumerate(lines, start=1):
            code = raw_line.split(";", 1)[0].rstrip()

            section_match = ASM_SECTION_RE.match(code)
            if section_match:
                current_section = section_match.group("name")
                section_sources.setdefault(current_section, set()).add(rel_path)
                continue

            include_match = ASM_INCLUDE_RE.match(code)
            if include_match and current_section is not None:
                include_path = include_match.group("path")
                section_sources.setdefault(current_section, set()).add(include_path)
                continue

            label_match = ASM_LABEL_RE.match(code)
            if not label_match:
                continue

            label = label_match.group("name")
            if label.startswith("."):
                if current_global is None:
                    continue
                label_key = f"{current_global}{label}"
            else:
                current_global = label
                label_key = label

            label_sources.setdefault(label_key, []).append(SourceLoc(rel_path, line_number))

    return label_sources, section_sources


def source_for(label_sources: dict[str, list[SourceLoc]], label: str) -> str:
    locs = label_sources.get(label)
    if not locs:
        return ""
    loc = locs[0]
    return f"`{loc.path}:{loc.line}`"


def format_symbol(symbols: dict[str, Symbol], label_sources: dict[str, list[SourceLoc]], name: str) -> str:
    symbol = symbols.get(name)
    source = source_for(label_sources, name)
    if symbol and source:
        return f"`{name}` ({bank_addr(symbol.bank, symbol.address)}, {source})"
    if symbol:
        return f"`{name}` ({bank_addr(symbol.bank, symbol.address)})"
    if source:
        return f"`{name}` ({source})"
    return f"`{name}`"


def section_source_summary(
    section: SectionEntry,
    section_sources: dict[str, set[str]],
    label_sources: dict[str, list[SourceLoc]],
) -> str:
    sources = set(section_sources.get(section.name, set()))
    for label in section.labels[:64]:
        for loc in label_sources.get(label, []):
            sources.add(loc.path)
    ordered = sorted(sources)
    if not ordered:
        return ""
    visible = ordered[:4]
    suffix = f", +{len(ordered) - len(visible)} more" if len(ordered) > len(visible) else ""
    return ", ".join(f"`{item}`" for item in visible) + suffix


def bank_free(sections: list[SectionEntry], empties: list[EmptyRange]) -> dict[tuple[str, int], int]:
    free: dict[tuple[str, int], int] = {}
    for section in sections:
        free.setdefault((section.memory, section.bank), 0)
    for empty in empties:
        key = (empty.memory, empty.bank)
        free[key] = free.get(key, 0) + empty.size
    return free


def estimate_boss_ai_trace_bytes() -> int:
    path = ROOT / "ram/wram.asm"
    if not path.exists():
        return 0

    total = 0
    in_trace = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        code = raw_line.split(";", 1)[0].strip()
        if code == "IF DEF(BOSS_AI_TRACE)":
            in_trace = True
            continue
        if in_trace and code == "ENDC":
            break
        if not in_trace or not code:
            continue

        parts = code.split()
        directive_index = next(
            (index for index, part in enumerate(parts) if part in {"db", "dw", "ds"}),
            None,
        )
        if directive_index is None:
            continue
        directive = parts[directive_index]
        args = " ".join(parts[directive_index + 1 :]).strip()
        if directive == "ds":
            try:
                total += int(args.split()[0], 0)
            except (IndexError, ValueError):
                pass
        elif directive == "db":
            total += len([arg for arg in args.split(",") if arg.strip()]) or 1
        elif directive == "dw":
            total += 2 * (len([arg for arg in args.split(",") if arg.strip()]) or 1)

    return total


def maybe_add_boss_ai_wram_budget(lines: list[str], symbols: dict[str, Symbol]) -> None:
    start = symbols.get("wBossAITier")
    end = symbols.get("wBossAIStateEnd")
    event_flags = symbols.get("wEventFlags")
    pending = symbols.get("wBossAIPendingPlayerSwitchCount")
    turns = symbols.get("wBossAITurnsElapsed")
    if not start or not end:
        return

    used = end.address - start.address
    free = BOSS_AI_RESERVED_BYTES - used
    trace_extra = estimate_boss_ai_trace_bytes()
    trace_used = used + trace_extra
    trace_free = BOSS_AI_RESERVED_BYTES - trace_used

    lines.extend(
        [
            "### Boss AI WRAM Reserve",
            "",
            "Boss AI state is carved out of full WRAMX bank 1 but has its own "
            "reserved block. Add Boss AI bytes here only after checking this budget.",
            "",
            "| Build | Used bytes | Reserved free bytes |",
            "| --- | ---: | ---: |",
            f"| Normal | {used} | {free} |",
            f"| With `BOSS_AI_TRACE` fields | {trace_used} | {trace_free} |",
            "",
            "| Label | Address | Use |",
            "| --- | --- | --- |",
            f"| `wBossAITier` | {bank_addr(start.bank, start.address)} | Boss AI state start |",
        ]
    )
    if pending:
        lines.append(
            f"| `wBossAIPendingPlayerSwitchCount` | "
            f"{bank_addr(pending.bank, pending.address)} | Current-turn switch input buffer |"
        )
    if turns:
        lines.append(
            f"| `wBossAITurnsElapsed` | {bank_addr(turns.bank, turns.address)} | "
            "Next-turn commit point for pending observations |"
        )
    lines.append(
        f"| `wBossAIStateEnd` | {bank_addr(end.bank, end.address)} | Logical end before reserve padding |"
    )
    if event_flags:
        lines.append(
            f"| `wEventFlags` | {bank_addr(event_flags.bank, event_flags.address)} | "
            "First unrelated field after reserved block |"
        )
    lines.append("")


def notable_sections(sections: list[SectionEntry]) -> list[SectionEntry]:
    result: list[SectionEntry] = []
    for section in sections:
        if section.name in NOTABLE_SECTIONS or any(
            section.name.startswith(prefix) for prefix in ("Map Scripts", "Songs")
        ):
            result.append(section)
    return result


def existing_paths(paths: tuple[str, ...]) -> list[str]:
    found: list[str] = []
    for path in paths:
        if (ROOT / path).exists():
            found.append(path)
    return found


def build_markdown(
    rom: str,
    summary: list[SummaryRow],
    sections: list[SectionEntry],
    empties: list[EmptyRange],
    symbols: dict[str, Symbol],
    label_sources: dict[str, list[SourceLoc]],
    section_sources: dict[str, set[str]],
    layout: dict[str, tuple[str, int | None]],
) -> str:
    lines: list[str] = [
        "# Developer ROM Index",
        "",
        "Boss AI cognition note: if you are here for the Boss AI loop, think "
        "wildly in the journal before changing source; this index is the hard "
        "memory/bank reality check for those ideas.",
        "",
        f"Generated: {date.today().isoformat()}",
        f"ROM target: `{rom}`",
        "",
        "Generated from `layout.link`, assembly sources, "
        f"`{rom}.map`, and `{rom}.sym`.",
        "",
        "Bank numbers are hexadecimal unless noted otherwise.",
        "",
        "Read `docs/README.md` first for helper-doc routing, then "
        "`docs/project_context.md` for design intent. This file is for "
        "navigation and memory planning only; it does not add anything to the ROM.",
        "",
        "## How To Use This Index",
        "",
        "1. Start with Quick Lookup for the subsystem you are changing.",
        "2. Use the anchor labels to jump from behavior to current bank/address and "
        "source line.",
        "3. Check Memory Summary and Tight Banks before adding code or data.",
        "4. Use Largest ROMX Free Ranges when moving optional code out of crowded "
        "banks.",
        "5. Refresh this file after a successful build changes linker outputs.",
        "",
        "## Quick Lookup",
        "",
    ]

    for area in AREAS:
        paths = existing_paths(area.paths)
        anchor_lines = [
            format_symbol(symbols, label_sources, name)
            for name in area.symbols
            if name in symbols or name in label_sources
        ]
        lines.append(f"### {area.title}")
        lines.append(f"- Intent: {area.intent}")
        if paths:
            lines.append("- Start here: " + ", ".join(f"`{path}`" for path in paths[:12]))
        else:
            lines.append("- Start here: no expected paths found.")
        if not area.symbols:
            pass
        elif anchor_lines:
            lines.append("- Anchors: " + "; ".join(anchor_lines[:14]))
        else:
            lines.append("- Anchors: no matching built symbols found in current output.")
        lines.append("")

    lines.extend(
        [
            "## Memory Summary",
            "",
            "| Region | Used | Free | Banks |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for row in summary:
        lines.append(
            f"| {row.memory} | {row.used} | {row.free} | "
            f"{row.banks if row.banks is not None else ''} |"
        )
    lines.append("")

    maybe_add_boss_ai_wram_budget(lines, symbols)

    free_by_bank = bank_free(sections, empties)
    tight_banks = sorted(
        ((memory, bank, free) for (memory, bank), free in free_by_bank.items() if memory in {"ROM0", "ROMX", "WRAM0", "WRAMX", "HRAM"}),
        key=lambda item: (item[2], item[0], item[1]),
    )[:18]

    lines.extend(
        [
            "### Tight Banks And Regions",
            "",
            "These are the first places to treat carefully when adding code or data.",
            "Bank numbers in this table are hexadecimal.",
            "",
            "| Region | Bank | Free bytes |",
            "| --- | ---: | ---: |",
        ]
    )
    for memory, bank, free in tight_banks:
        lines.append(f"| {memory} | {bank:02x} | {free} |")
    lines.append("")

    largest_free = sorted(
        (empty for empty in empties if empty.memory == "ROMX"),
        key=lambda item: item.size,
        reverse=True,
    )[:14]
    lines.extend(
        [
            "### Largest ROMX Free Ranges",
            "",
            "Use these as candidates when moving optional code or data out of tight banks.",
            "",
            "| Bank | Range | Bytes |",
            "| ---: | --- | ---: |",
        ]
    )
    for empty in largest_free:
        lines.append(f"| {empty.bank:02x} | {hex4(empty.start)}-{hex4(empty.end)} | {empty.size} |")
    lines.append("")

    lines.extend(
        [
            "## Notable Sections",
            "",
            "| Section | Region | Bank/range | Size | Layout constraint | Source hints |",
            "| --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for section in notable_sections(sections):
        layout_memory, layout_bank = layout.get(section.name, ("", None))
        constraint = (
            f"{layout_memory} {layout_bank:02x}" if layout_memory and layout_bank is not None else layout_memory
        )
        source_summary = section_source_summary(section, section_sources, label_sources)
        lines.append(
            f"| `{section.name}` | {section.memory} | {bank_range(section)} | "
            f"{section.size} | {constraint} | {source_summary} |"
        )
    lines.append("")

    important_names = []
    for area in AREAS:
        for name in area.symbols:
            if name not in important_names and (name in symbols or name in label_sources):
                important_names.append(name)

    lines.extend(
        [
            "## Important Labels",
            "",
            "| Label | Address | Source |",
            "| --- | --- | --- |",
        ]
    )
    for name in important_names:
        symbol = symbols.get(name)
        address = bank_addr(symbol.bank, symbol.address) if symbol else ""
        lines.append(f"| `{name}` | {address} | {source_for(label_sources, name)} |")
    lines.append("")

    lines.extend(
        [
            "## Warning Zones",
            "",
            "- ROM0, WRAM0, WRAMX, and HRAM are global pressure points. Prefer moving "
            "new optional logic into ROMX banks with room.",
            "- Battle-sensitive sections such as `Battle Core`, `Effect Commands`, "
            "`Enemy Trainers`, and `Late Gen Held Items` should be checked in this "
            "file after every substantial mechanics change.",
            "- Generated files should be refreshed with "
            "`python scripts/generate_dev_index.py --rom pokegold` after linker "
            "addresses change.",
            "- If this file disagrees with source after a build, regenerate it before "
            "using addresses for planning.",
            "",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", default="pokegold", help="ROM basename to read, without extension.")
    parser.add_argument(
        "--out",
        default="docs/generated/dev_index.md",
        help="Output Markdown path, relative to the repo root unless absolute.",
    )
    args = parser.parse_args()

    map_path = ROOT / f"{args.rom}.map"
    sym_path = ROOT / f"{args.rom}.sym"
    layout_path = ROOT / "layout.link"
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = ROOT / out_path

    for required_path in (map_path, sym_path, layout_path):
        if not required_path.exists():
            print(f"error: missing required input: {required_path}", file=sys.stderr)
            return 1

    summary, sections, empties = parse_map(map_path)
    symbols = parse_sym(sym_path)
    layout = parse_layout(layout_path)
    label_sources, section_sources = parse_source_indexes(iter_asm_files())

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        build_markdown(
            rom=args.rom,
            summary=summary,
            sections=sections,
            empties=empties,
            symbols=symbols,
            label_sources=label_sources,
            section_sources=section_sources,
            layout=layout,
        ),
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {out_path.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
