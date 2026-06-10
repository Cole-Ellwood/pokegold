from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
import json
import re

from scripts.generate_dev_index import EmptyRange, SectionEntry, Symbol, parse_map, parse_sym

from .address import parse_address_int, parse_address_spec
from .catalog import ROOT
from .report_envelope import sha256_file


ASM_SECTION_RE = re.compile(r'^\s*SECTION\s+"(?P<name>[^"]+)"')
ASM_INCLUDE_RE = re.compile(r'^\s*INCLUDE\s+"(?P<path>[^"]+)"')
ASM_LABEL_RE = re.compile(r"^\s*(?P<name>[A-Za-z_.$][A-Za-z0-9_.$]*)\s*:{1,2}")
ASM_BARE_LOCAL_LABEL_RE = re.compile(r"^\s*(?P<name>\.[A-Za-z_.$][A-Za-z0-9_.$]*)\s*$")
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


@dataclass(frozen=True)
class SourceLoc:
    path: str
    line: int


@dataclass(frozen=True)
class RomByteTarget:
    bank: int
    address: int
    offset: int
    source: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "bank": self.bank,
            "bank_hex": f"{self.bank:02X}",
            "address": self.address,
            "address_hex": f"{self.address:04X}",
            "bank_address": f"{self.bank:02X}:{self.address:04X}",
            "offset": self.offset,
            "offset_hex": f"0x{self.offset:X}",
            "source": self.source,
        }


def build_rom_byte_lookup_report(
    *,
    address: str = "",
    offset: str = "",
    rom_path: Path | str = "pokegold.gbc",
    symbols_path: Path | str = "pokegold.sym",
    map_path: Path | str = "pokegold.map",
    root: Path = ROOT,
) -> dict[str, Any]:
    rom = resolve_path(rom_path, root=root)
    symbols = resolve_path(symbols_path, root=root)
    map_file = resolve_path(map_path, root=root)
    errors: list[str] = []
    warnings: list[str] = []
    target: RomByteTarget | None = None
    rom_byte: dict[str, Any] = {}
    if not address and not offset:
        errors.append("one of --address or --offset is required")
    if address and offset:
        errors.append("--address and --offset are mutually exclusive")
    if not errors:
        try:
            if address:
                target = target_from_address(address)
            else:
                target = target_from_offset(offset)
        except ValueError as exc:
            errors.append(str(exc))
    errors.extend(missing_input_errors(rom=rom, symbols=symbols, map_file=map_file, root=root))
    if target is not None and rom.exists() and rom.is_file():
        rom_byte = read_rom_byte(rom, target)
        if not rom_byte:
            errors.append(
                "resolved offset is beyond the ROM file size: "
                f"0x{target.offset:X} >= 0x{rom.stat().st_size:X}"
            )

    lookup = empty_lookup()
    sections: list[SectionEntry] = []
    empties: list[EmptyRange] = []
    symbols_by_name: dict[str, Symbol] = {}
    label_sources: dict[str, list[SourceLoc]] = {}
    section_sources: dict[str, set[str]] = {}
    if not errors and target is not None:
        _, sections, empties = parse_map(map_file)
        symbols_by_name = parse_sym(symbols)
        label_sources, section_sources = parse_source_indexes(collect_asm_files(root), root=root)
        lookup = lookup_rom_byte(
            target,
            sections=sections,
            empties=empties,
            symbols_by_name=symbols_by_name,
            label_sources=label_sources,
            section_sources=section_sources,
            root=root,
        )

    return {
        "schema_version": 1,
        "kind": "unified_debugger_rom_byte_lookup",
        "valid": not errors,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "query": {
            "address": address,
            "offset": offset,
            "rom": display_path(rom, root=root),
            "symbols": display_path(symbols, root=root),
            "map": display_path(map_file, root=root),
        },
        "input_hashes": {
            "rom_sha256": sha256_file(rom),
            "symbols_sha256": sha256_file(symbols),
            "map_sha256": sha256_file(map_file),
        },
        "target": target.as_dict() if target is not None else {},
        "rom_byte": rom_byte,
        "lookup": lookup,
        "index_summary": {
            "section_count": len(sections),
            "empty_range_count": len(empties),
            "symbol_count": len(symbols_by_name),
            "source_label_count": len(label_sources),
            "section_source_count": len(section_sources),
        },
        "known_limits": [
            "This is a linker/symbol/source lookup, not a dynamic execution proof.",
            "Nearest-label ownership is low confidence unless exact symbol/source or content-mirror evidence covers the byte.",
            "Content-mirror exact byte spans are not normalized into this index yet.",
        ],
    }


def build_rom_index_report(
    *,
    rom_path: Path | str = "pokegold.gbc",
    symbols_path: Path | str = "pokegold.sym",
    map_path: Path | str = "pokegold.map",
    root: Path = ROOT,
    surface_index_out: Path | str = "",
    byte_index_out: Path | str = "",
    content_mirror_report_path: Path | str = "",
) -> dict[str, Any]:
    rom = resolve_path(rom_path, root=root)
    symbols = resolve_path(symbols_path, root=root)
    map_file = resolve_path(map_path, root=root)
    errors = missing_input_errors(rom=rom, symbols=symbols, map_file=map_file, root=root)
    warnings: list[str] = []
    sections: list[SectionEntry] = []
    empties: list[EmptyRange] = []
    symbols_by_name: dict[str, Symbol] = {}
    label_sources: dict[str, list[SourceLoc]] = {}
    section_sources: dict[str, set[str]] = {}
    surface_rows: list[dict[str, Any]] = []
    byte_rows: list[dict[str, Any]] = []
    content_mirror_rows: list[dict[str, Any]] = []
    input_hashes = {
        "rom_sha256": sha256_file(rom),
        "symbols_sha256": sha256_file(symbols),
        "map_sha256": sha256_file(map_file),
    }
    if not errors:
        _, sections, empties = parse_map(map_file)
        symbols_by_name = parse_sym(symbols)
        label_sources, section_sources = parse_source_indexes(collect_asm_files(root), root=root)
        surface_rows = build_surface_index_rows(
            sections=sections,
            empties=empties,
            symbols_by_name=symbols_by_name,
            label_sources=label_sources,
            section_sources=section_sources,
            input_hashes=input_hashes,
        )
        byte_rows = build_byte_index_rows(
            sections=sections,
            empties=empties,
            symbols_by_name=symbols_by_name,
            label_sources=label_sources,
            section_sources=section_sources,
            input_hashes=input_hashes,
        )
        content_mirror_rows = load_content_mirror_byte_rows(content_mirror_report_path, root=root)
        for row in content_mirror_rows:
            row["input_hashes"] = dict(input_hashes)
        byte_rows.extend(content_mirror_rows)
    surface_path = resolve_optional_output(surface_index_out, root=root)
    byte_path = resolve_optional_output(byte_index_out, root=root)
    written_outputs: dict[str, Any] = {
        "surface_index_out": "",
        "byte_index_out": "",
        "surface_index_written": False,
        "byte_index_written": False,
    }
    if not errors and surface_path is not None:
        write_jsonl(surface_path, surface_rows)
        written_outputs["surface_index_out"] = display_path(surface_path, root=root)
        written_outputs["surface_index_written"] = True
    if not errors and byte_path is not None:
        write_jsonl(byte_path, byte_rows)
        written_outputs["byte_index_out"] = display_path(byte_path, root=root)
        written_outputs["byte_index_written"] = True

    return {
        "schema_version": 1,
        "kind": "unified_debugger_rom_index",
        "valid": not errors,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "query": {
            "rom": display_path(rom, root=root),
            "symbols": display_path(symbols, root=root),
            "map": display_path(map_file, root=root),
            "content_mirror_report": (
                display_path(resolve_path(content_mirror_report_path, root=root), root=root)
                if content_mirror_report_path
                else ""
            ),
        },
        "input_hashes": input_hashes,
        "index_summary": {
            "section_count": len(sections),
            "empty_range_count": len(empties),
            "symbol_count": len(symbols_by_name),
            "source_label_count": len(label_sources),
            "section_source_count": len(section_sources),
            "surface_row_count": len(surface_rows),
            "byte_span_row_count": len(byte_rows),
            "content_mirror_exact_span_count": len(content_mirror_rows),
            "unowned_surface_row_count": sum(1 for row in surface_rows if row.get("owner_lane") == ""),
            "low_confidence_byte_span_count": sum(
                1
                for row in byte_rows
                if row.get("confidence") in {"nearest_label_span", "section_owned", "unowned_section"}
            ),
        },
        "outputs": written_outputs,
        "surface_samples": surface_rows[:5],
        "byte_span_samples": byte_rows[:5],
        "known_limits": [
            "The surface index covers linker sections, symbols, and empty ROM ranges; map/script/asset behavioral surfaces still need specialized expansion.",
            "Byte-index label spans are navigation ownership, not proof that every byte in the span was emitted by the nearest label.",
            "Content-mirror exact byte spans are not normalized into this index yet.",
        ],
    }


def lookup_rom_byte(
    target: RomByteTarget,
    *,
    sections: list[SectionEntry],
    empties: list[EmptyRange],
    symbols_by_name: dict[str, Symbol],
    label_sources: dict[str, list[SourceLoc]],
    section_sources: dict[str, set[str]],
    root: Path,
) -> dict[str, Any]:
    section = find_section(target, sections)
    empty = find_empty(target, empties)
    exact_symbols = [
        symbol
        for symbol in symbols_by_name.values()
        if symbol.bank == target.bank and symbol.address == target.address
    ]
    exact_candidates = [
        symbol_candidate(symbol, label_sources=label_sources, confidence="exact_symbol_start")
        for symbol in exact_symbols
        if label_sources.get(symbol.name)
    ]
    if exact_candidates:
        return {
            "confidence": "exact_symbol_start",
            "confidence_rank": 90,
            "reason": "byte is exactly at a symbol address with a source definition",
            "section": section_row(section) if section else {},
            "empty_range": {},
            "best": exact_candidates[0],
            "candidates": exact_candidates,
        }
    if empty is not None:
        return {
            "confidence": "empty_or_padding",
            "confidence_rank": 10,
            "reason": "byte lies in an EMPTY linker range",
            "section": {},
            "empty_range": empty_row(empty),
            "best": {},
            "candidates": [],
        }
    if section is None:
        return {
            "confidence": "unowned_section",
            "confidence_rank": 0,
            "reason": "no linker section covers this byte",
            "section": {},
            "empty_range": {},
            "best": {},
            "candidates": [],
        }
    nearest = nearest_symbol(target, symbols_by_name.values(), section=section)
    if nearest is not None:
        candidate = symbol_candidate(nearest, label_sources=label_sources, confidence="nearest_label")
        if candidate["source_refs"]:
            candidate["distance_bytes"] = target.address - nearest.address
            return {
                "confidence": "nearest_label",
                "confidence_rank": 40,
                "reason": "byte is inside a section after the nearest prior symbol; use for navigation only",
                "section": section_row(section, section_sources=section_sources, label_sources=label_sources),
                "empty_range": {},
                "best": candidate,
                "candidates": [candidate],
            }
    section_candidate = section_candidate_row(
        section,
        section_sources=section_sources,
        label_sources=label_sources,
    )
    if section_candidate.get("source_refs"):
        return {
            "confidence": "section_owned",
            "confidence_rank": 30,
            "reason": "byte is inside a linker section with source ownership, but no nearer symbol was found",
            "section": section_row(section, section_sources=section_sources, label_sources=label_sources),
            "empty_range": {},
            "best": section_candidate,
            "candidates": [section_candidate],
        }
    return {
        "confidence": "unowned_section",
        "confidence_rank": 20,
        "reason": "byte is inside a linker section without source ownership in the current index",
        "section": section_row(section),
        "empty_range": {},
        "best": {},
        "candidates": [],
    }


def build_surface_index_rows(
    *,
    sections: list[SectionEntry],
    empties: list[EmptyRange],
    symbols_by_name: dict[str, Symbol],
    label_sources: dict[str, list[SourceLoc]],
    section_sources: dict[str, set[str]],
    input_hashes: dict[str, str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for section in sections:
        if section.memory not in {"ROM0", "ROMX"}:
            continue
        refs = section_source_refs(
            section,
            section_sources=section_sources,
            label_sources=label_sources,
        )
        rows.append(
            base_index_row(
                kind="linker_section",
                surface_id=f"section:{section.memory}:{section.bank:02X}:{section.start:04X}-{section.end:04X}:{slug(section.name)}",
                section=section,
                source_refs=refs,
                confidence="section_owned" if refs else "unowned_section",
                owner_lane="source_rom_provenance" if refs else "",
                unsupported_reason="" if refs else "missing_source_refs",
                input_hashes=input_hashes,
            )
        )
    for symbol in sorted(symbols_by_name.values(), key=lambda item: (item.bank, item.address, item.name)):
        section = find_section_for_bank_address(symbol.bank, symbol.address, sections)
        if section is None:
            continue
        refs = source_refs_for_label(symbol.name, label_sources=label_sources)
        rows.append(
            base_index_row(
                kind="symbol",
                surface_id=f"symbol:{symbol.bank:02X}:{symbol.address:04X}:{symbol.name}",
                section=section,
                source_refs=refs,
                confidence="exact_symbol_start" if refs else "symbol_without_source",
                owner_lane="source_rom_provenance" if refs else "",
                unsupported_reason="" if refs else "missing_source_refs",
                input_hashes=input_hashes,
                label=symbol.name,
                span_start=symbol.address,
                span_end=symbol.address,
            )
        )
    for empty in empties:
        if empty.memory not in {"ROM0", "ROMX"}:
            continue
        rows.append(
            {
                "schema_version": 1,
                "kind": "rom_surface_index_row",
                "surface_id": f"empty:{empty.memory}:{empty.bank:02X}:{empty.start:04X}-{empty.end:04X}",
                "surface_kind": "empty_range",
                "owner_lane": "source_rom_provenance",
                "proof_capability": "rom-byte",
                "reachable": False,
                "reachable_status": "empty_or_padding",
                "unsupported_reason": "empty linker range",
                "source_refs": [],
                "rom_span": rom_span_row(empty.bank, empty.start, empty.end),
                "section": "",
                "nearest_label": "",
                "confidence": "empty_or_padding",
                "ambiguity_notes": ["padding/free-space range reported by linker map"],
                "input_hashes": input_hashes,
            }
        )
    return sorted(rows, key=lambda item: item["surface_id"])


def build_byte_index_rows(
    *,
    sections: list[SectionEntry],
    empties: list[EmptyRange],
    symbols_by_name: dict[str, Symbol],
    label_sources: dict[str, list[SourceLoc]],
    section_sources: dict[str, set[str]],
    input_hashes: dict[str, str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    symbols_by_bank = group_rom_symbols(symbols_by_name.values(), sections)
    for section in sections:
        if section.memory not in {"ROM0", "ROMX"} or section.size <= 0:
            continue
        section_symbols = [
            symbol
            for symbol in symbols_by_bank.get(section.bank, [])
            if section.start <= symbol.address <= section.end
        ]
        if not section_symbols:
            rows.append(section_byte_span_row(section, section.start, section.end, section_sources, label_sources, input_hashes))
            continue
        if section.start < section_symbols[0].address:
            rows.append(
                section_byte_span_row(
                    section,
                    section.start,
                    section_symbols[0].address - 1,
                    section_sources,
                    label_sources,
                    input_hashes,
                )
            )
        for index, symbol in enumerate(section_symbols):
            end = section.end
            if index + 1 < len(section_symbols):
                end = min(end, section_symbols[index + 1].address - 1)
            if end < symbol.address:
                continue
            refs = source_refs_for_label(symbol.name, label_sources=label_sources)
            rows.append(
                {
                    "schema_version": 1,
                    "kind": "rom_byte_index_row",
                    "row_id": f"span:{symbol.bank:02X}:{symbol.address:04X}-{end:04X}:{symbol.name}",
                    "rom_span": rom_span_row(symbol.bank, symbol.address, end),
                    "section": section.name,
                    "section_kind": section.memory,
                    "nearest_label": symbol.name,
                    "source_refs": refs,
                    "confidence": "nearest_label_span" if refs else "section_owned",
                    "ambiguity_notes": [
                        "nearest-label span ends at next symbol or section end; exact ownership of interior bytes is not proven"
                    ],
                    "input_hashes": input_hashes,
                }
            )
    for empty in empties:
        if empty.memory not in {"ROM0", "ROMX"}:
            continue
        rows.append(
            {
                "schema_version": 1,
                "kind": "rom_byte_index_row",
                "row_id": f"empty:{empty.bank:02X}:{empty.start:04X}-{empty.end:04X}",
                "rom_span": rom_span_row(empty.bank, empty.start, empty.end),
                "section": "",
                "section_kind": empty.memory,
                "nearest_label": "",
                "source_refs": [],
                "confidence": "empty_or_padding",
                "ambiguity_notes": ["padding/free-space range reported by linker map"],
                "input_hashes": input_hashes,
            }
        )
    return sorted(rows, key=lambda item: (item["rom_span"]["offset_start"], item["row_id"]))


def load_content_mirror_byte_rows(path: Path | str, *, root: Path) -> list[dict[str, Any]]:
    if path in {"", None}:
        return []
    resolved = resolve_path(path, root=root)
    if not resolved.exists() or not resolved.is_file():
        return []
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    rows = payload.get("byte_span_rows", [])
    if not isinstance(rows, list):
        return []
    return [
        dict(row)
        for row in rows
        if isinstance(row, dict) and row.get("confidence") == "content_mirror_exact_span"
    ]


def target_from_address(value: str) -> RomByteTarget:
    spec = parse_address_spec(value)
    if spec.space == "romx" and spec.bank is None:
        raise ValueError("ROMX address lookup requires a bank prefix, e.g. 0E:542B")
    if spec.space not in {"rom0", "romx"}:
        raise ValueError(f"rom-byte only supports ROM addresses, got {spec.space}")
    bank = spec.bank if spec.bank is not None else 0
    return RomByteTarget(
        bank=bank,
        address=spec.address,
        offset=rom_offset(bank, spec.address),
        source="address",
    )


def target_from_offset(value: str) -> RomByteTarget:
    offset = parse_address_int(value)
    if offset < 0:
        raise ValueError("offset must be non-negative")
    bank, address = bank_address_from_offset(offset)
    return RomByteTarget(bank=bank, address=address, offset=offset, source="offset")


def rom_offset(bank: int, address: int) -> int:
    if bank == 0 and 0 <= address < 0x4000:
        return address
    if bank >= 1 and 0x4000 <= address < 0x8000:
        return bank * 0x4000 + (address - 0x4000)
    raise ValueError(f"not a valid ROM bank/address: {bank:02X}:{address:04X}")


def bank_address_from_offset(offset: int) -> tuple[int, int]:
    if offset < 0x4000:
        return 0, offset
    bank = offset // 0x4000
    if bank > 0xFF:
        raise ValueError("offset resolves beyond max ROM bank 0xFF")
    return bank, 0x4000 + (offset % 0x4000)


def read_rom_byte(rom: Path, target: RomByteTarget) -> dict[str, Any]:
    if target.offset < 0:
        return {}
    size = rom.stat().st_size
    if target.offset >= size:
        return {}
    with rom.open("rb") as handle:
        handle.seek(target.offset)
        value = handle.read(1)
    if not value:
        return {}
    byte = value[0]
    return {
        "offset": target.offset,
        "offset_hex": f"0x{target.offset:X}",
        "value": byte,
        "value_hex": f"{byte:02X}",
    }


def find_section(target: RomByteTarget, sections: Iterable[SectionEntry]) -> SectionEntry | None:
    for section in sections:
        if section.memory not in {"ROM0", "ROMX"}:
            continue
        if section.size <= 0:
            continue
        if section.bank == target.bank and section.start <= target.address <= section.end:
            return section
    return None


def find_section_for_bank_address(
    bank: int,
    address: int,
    sections: Iterable[SectionEntry],
) -> SectionEntry | None:
    for section in sections:
        if section.memory not in {"ROM0", "ROMX"} or section.size <= 0:
            continue
        if section.bank == bank and section.start <= address <= section.end:
            return section
    return None


def find_empty(target: RomByteTarget, empties: Iterable[EmptyRange]) -> EmptyRange | None:
    for empty in empties:
        if empty.memory not in {"ROM0", "ROMX"}:
            continue
        if empty.bank == target.bank and empty.start <= target.address <= empty.end:
            return empty
    return None


def nearest_symbol(
    target: RomByteTarget,
    symbols: Iterable[Symbol],
    *,
    section: SectionEntry,
) -> Symbol | None:
    candidates = [
        symbol
        for symbol in symbols
        if symbol.bank == target.bank and section.start <= symbol.address <= target.address
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: item.address)[-1]


def symbol_candidate(
    symbol: Symbol,
    *,
    label_sources: dict[str, list[SourceLoc]],
    confidence: str,
) -> dict[str, Any]:
    source_refs = source_refs_for_label(symbol.name, label_sources=label_sources)
    return {
        "kind": "symbol",
        "confidence": confidence,
        "label": symbol.name,
        "bank_address": f"{symbol.bank:02X}:{symbol.address:04X}",
        "source_refs": source_refs,
    }


def section_candidate_row(
    section: SectionEntry,
    *,
    section_sources: dict[str, set[str]],
    label_sources: dict[str, list[SourceLoc]],
) -> dict[str, Any]:
    return {
        "kind": "section",
        "confidence": "section_owned",
        "section": section.name,
        "bank_range": f"{section.bank:02X}:{section.start:04X}-{section.end:04X}",
        "source_refs": section_source_refs(section, section_sources=section_sources, label_sources=label_sources),
    }


def section_row(
    section: SectionEntry | None,
    *,
    section_sources: dict[str, set[str]] | None = None,
    label_sources: dict[str, list[SourceLoc]] | None = None,
) -> dict[str, Any]:
    if section is None:
        return {}
    row = {
        "memory": section.memory,
        "bank": section.bank,
        "start": section.start,
        "end": section.end,
        "bank_range": f"{section.bank:02X}:{section.start:04X}-{section.end:04X}",
        "size": section.size,
        "name": section.name,
        "labels": list(section.labels),
    }
    if section_sources is not None and label_sources is not None:
        row["source_refs"] = section_source_refs(
            section,
            section_sources=section_sources,
            label_sources=label_sources,
        )
    return row


def empty_row(empty: EmptyRange) -> dict[str, Any]:
    return {
        "memory": empty.memory,
        "bank": empty.bank,
        "start": empty.start,
        "end": empty.end,
        "bank_range": f"{empty.bank:02X}:{empty.start:04X}-{empty.end:04X}",
        "size": empty.size,
    }


def source_refs_for_label(label: str, *, label_sources: dict[str, list[SourceLoc]]) -> list[dict[str, Any]]:
    return [
        {"path": loc.path, "line": loc.line, "kind": "definition"}
        for loc in label_sources.get(label, [])
    ]


def section_source_refs(
    section: SectionEntry,
    *,
    section_sources: dict[str, set[str]],
    label_sources: dict[str, list[SourceLoc]],
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    seen: set[tuple[str, int | None, str]] = set()
    for path in sorted(section_sources.get(section.name, set())):
        key = (path, None, "section_source")
        if key not in seen:
            seen.add(key)
            refs.append({"path": path, "line": None, "kind": "section_source"})
    for label in section.labels[:64]:
        for loc in label_sources.get(label, []):
            key = (loc.path, loc.line, "label")
            if key not in seen:
                seen.add(key)
                refs.append({"path": loc.path, "line": loc.line, "kind": "label"})
    return refs[:20]


def base_index_row(
    *,
    kind: str,
    surface_id: str,
    section: SectionEntry,
    source_refs: list[dict[str, Any]],
    confidence: str,
    owner_lane: str,
    unsupported_reason: str,
    input_hashes: dict[str, str],
    label: str = "",
    span_start: int | None = None,
    span_end: int | None = None,
) -> dict[str, Any]:
    start = section.start if span_start is None else span_start
    end = section.end if span_end is None else span_end
    return {
        "schema_version": 1,
        "kind": "rom_surface_index_row",
        "surface_id": surface_id,
        "surface_kind": kind,
        "owner_lane": owner_lane,
        "proof_capability": "rom-byte",
        "reachable": True,
        "reachable_status": "linked",
        "unsupported_reason": unsupported_reason,
        "source_refs": source_refs,
        "rom_span": rom_span_row(section.bank, start, end),
        "section": section.name,
        "nearest_label": label,
        "confidence": confidence,
        "ambiguity_notes": ambiguity_notes_for_confidence(confidence),
        "input_hashes": input_hashes,
    }


def section_byte_span_row(
    section: SectionEntry,
    start: int,
    end: int,
    section_sources: dict[str, set[str]],
    label_sources: dict[str, list[SourceLoc]],
    input_hashes: dict[str, str],
) -> dict[str, Any]:
    refs = section_source_refs(section, section_sources=section_sources, label_sources=label_sources)
    return {
        "schema_version": 1,
        "kind": "rom_byte_index_row",
        "row_id": f"section:{section.bank:02X}:{start:04X}-{end:04X}:{slug(section.name)}",
        "rom_span": rom_span_row(section.bank, start, end),
        "section": section.name,
        "section_kind": section.memory,
        "nearest_label": "",
        "source_refs": refs,
        "confidence": "section_owned" if refs else "unowned_section",
        "ambiguity_notes": ambiguity_notes_for_confidence("section_owned" if refs else "unowned_section"),
        "input_hashes": input_hashes,
    }


def rom_span_row(bank: int, start: int, end: int) -> dict[str, Any]:
    offset_start = safe_rom_offset(bank, start)
    offset_end = safe_rom_offset(bank, end)
    return {
        "bank": bank,
        "bank_hex": f"{bank:02X}",
        "address_start": start,
        "address_end": end,
        "address_start_hex": f"{start:04X}",
        "address_end_hex": f"{end:04X}",
        "bank_range": f"{bank:02X}:{start:04X}-{end:04X}",
        "offset_start": offset_start,
        "offset_end": offset_end,
        "offset_start_hex": f"0x{offset_start:X}" if offset_start >= 0 else "",
        "offset_end_hex": f"0x{offset_end:X}" if offset_end >= 0 else "",
        "size": max(0, end - start + 1),
    }


def safe_rom_offset(bank: int, address: int) -> int:
    try:
        return rom_offset(bank, address)
    except ValueError:
        return -1


def group_rom_symbols(
    symbols: Iterable[Symbol],
    sections: Iterable[SectionEntry],
) -> dict[int, list[Symbol]]:
    by_bank: dict[int, list[Symbol]] = {}
    for symbol in symbols:
        if find_section_for_bank_address(symbol.bank, symbol.address, sections) is None:
            continue
        by_bank.setdefault(symbol.bank, []).append(symbol)
    for bank, rows in by_bank.items():
        by_bank[bank] = sorted(rows, key=lambda item: (item.address, item.name))
    return by_bank


def ambiguity_notes_for_confidence(confidence: str) -> list[str]:
    if confidence == "exact_symbol_start":
        return []
    if confidence == "nearest_label_span":
        return ["nearest-label ownership is for navigation; exact interior byte ownership needs parser/content evidence"]
    if confidence == "section_owned":
        return ["section source is known, but exact byte ownership is not proven"]
    if confidence == "unowned_section":
        return ["no source owner was found for this linked range"]
    if confidence == "symbol_without_source":
        return ["symbol exists in linker output but no source definition was found"]
    return []


def slug(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return text.strip("_") or "unnamed"


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def resolve_optional_output(path: Path | str, *, root: Path) -> Path | None:
    if path in {"", None}:
        return None
    return resolve_path(path, root=root)


def parse_source_indexes(
    asm_files: Iterable[Path],
    *,
    root: Path,
) -> tuple[dict[str, list[SourceLoc]], dict[str, set[str]]]:
    label_sources: dict[str, list[SourceLoc]] = {}
    section_sources: dict[str, set[str]] = {}
    for path in asm_files:
        current_global: str | None = None
        current_section: str | None = None
        rel_path = display_path(path, root=root)
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for line_number, raw_line in enumerate(lines, start=1):
            code = raw_line.split(";", 1)[0].rstrip()
            section_match = ASM_SECTION_RE.match(code)
            if section_match:
                current_section = section_match.group("name")
                section_sources.setdefault(current_section, set()).add(rel_path)
                continue
            include_match = ASM_INCLUDE_RE.match(code)
            if include_match and current_section is not None:
                section_sources.setdefault(current_section, set()).add(include_match.group("path"))
                continue
            label_match = ASM_LABEL_RE.match(code)
            if not label_match:
                label_match = ASM_BARE_LOCAL_LABEL_RE.match(code)
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


def collect_asm_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.asm"):
        try:
            rel_parts = path.relative_to(root).parts
        except ValueError:
            continue
        if any(part in EXCLUDED_DIRS for part in rel_parts):
            continue
        files.append(path)
    return sorted(files, key=lambda item: display_path(item, root=root))


def missing_input_errors(*, rom: Path, symbols: Path, map_file: Path, root: Path) -> list[str]:
    errors = []
    for label, path in (("rom", rom), ("symbols", symbols), ("map", map_file)):
        if not path.exists():
            errors.append(f"missing {label} file: {display_path(path, root=root)}")
        elif not path.is_file():
            errors.append(f"{label} path is not a file: {display_path(path, root=root)}")
    return errors


def empty_lookup() -> dict[str, Any]:
    return {
        "confidence": "missing_input",
        "confidence_rank": 0,
        "reason": "",
        "section": {},
        "empty_range": {},
        "best": {},
        "candidates": [],
    }


def resolve_path(path: Path | str, *, root: Path) -> Path:
    resolved = Path(path)
    if resolved.is_absolute():
        return resolved
    return root / resolved


def display_path(path: Path, *, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()
