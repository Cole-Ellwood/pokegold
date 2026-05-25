"""Top-level orchestrator: per-file dispatch across every content type."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..catalog import ROOT
from ..provenance import display_path, resolve_path
from ..workflow import command_is_runnable
from .asset_tables import asset_table_rom_mirror_invariants
from .audio import audio_channel_invariants, audio_channel_rom_mirror_invariants, parse_channel_blocks
from .helpers import (
    ALLOWED_DATA_BLOCK_DIRECTIVES,
    ALLOWED_INCBIN_TABLE_DIRECTIVES,
    DATA_BYTE_DIRECTIVES,
    DATA_STRING_CONTINUATION_DIRECTIVES,
    DEF_EQUS_RE,
    content_invariant,
    first_token,
    parse_incbin_entries,
    source_commands,
    split_label,
    split_macro_args,
    strip_comment,
    symbol_name_for_label,
    unique_list,
)
from .incbin import asset_invariants, asset_rom_mirror_invariants
from .labeled_data import data_block_rom_mirror_invariants
from .maps import (
    MAP_SECTION_MACROS,
    count_object_constants,
    is_map_event_file,
    map_event_invariants,
    map_event_rom_mirror_invariants,
    object_constant_invariants,
)
from .movement import movement_data_rom_mirror_invariants, parse_movement_blocks
from .rom_context import DEFAULT_ROM_PATH, DEFAULT_SYMBOLS_PATH, load_rom_mirror_context, parse_source_constants
from .scripts import parse_script_blocks, script_command_rom_mirror_invariants
from .text import parse_text_blocks, text_block_rom_mirror_invariants


CONTENT_ROOTS = (
    "maps",
    "data",
    "gfx",
    "audio",
    "text",
    "scripts",
    "engine/events",
    "engine/gfx",
    "engine/menus",
    "engine/overworld",
)
ROM_MIRROR_INVARIANT_TYPES = {
    "map_event_rom_bytes",
    "incbin_asset_rom_bytes",
    "incbin_table_rom_bytes",
    "audio_channel_rom_bytes",
    "labeled_data_rom_bytes",
    "script_command_rom_bytes",
    "text_block_rom_bytes",
    "movement_data_rom_bytes",
}


def build_content_mirror_report(
    *,
    source_files: tuple[str, ...] = (),
    changed_files: tuple[str, ...] = (),
    max_files: int = 120,
    rom_path: str = DEFAULT_ROM_PATH,
    symbols_path: str = DEFAULT_SYMBOLS_PATH,
    root: Path = ROOT,
) -> dict[str, Any]:
    limit = max(1, int(max_files))
    requested = unique_list([*source_files, *changed_files])
    auto_scanned = False
    if not requested:
        requested = auto_content_sources(root=root, max_files=limit)
        auto_scanned = True

    source_reports: list[dict[str, Any]] = []
    invariants: list[dict[str, Any]] = []
    errors: list[str] = []
    warnings: list[str] = []
    label_occurrences: dict[str, list[dict[str, Any]]] = {}
    rom_context = load_rom_mirror_context(rom_path=rom_path, symbols_path=symbols_path, root=root)

    for raw_path in requested[:limit]:
        source_report = analyze_source_file(raw_path, root=root, rom_context=rom_context)
        source_reports.append(source_report)
        invariants.extend(source_report.get("invariants", []))
        errors.extend(source_report.get("errors", []))
        warnings.extend(source_report.get("warnings", []))
        for label in source_report.get("global_labels", []):
            label_occurrences.setdefault(label["label"], []).append(
                {
                    "source_file": source_report["path"],
                    "line": label["line"],
                }
            )

    invariants.extend(duplicate_label_invariants(label_occurrences))
    warnings.extend(
        invariant["title"]
        for invariant in invariants
        if invariant.get("status") == "warning"
    )

    failed = [item for item in invariants if item.get("status") == "failed"]
    warning_invariants = [item for item in invariants if item.get("status") == "warning"]
    passed = [item for item in invariants if item.get("status") == "passed"]
    rom_mirrors = [item for item in invariants if is_rom_mirror_invariant(item)]
    failed_rom_mirrors = [item for item in rom_mirrors if item.get("status") == "failed"]
    warning_rom_mirrors = [item for item in rom_mirrors if item.get("status") == "warning"]
    passed_rom_mirrors = [item for item in rom_mirrors if item.get("status") == "passed"]
    commands = unique_list(
        [
            *[
                command
                for source in source_reports
                for command in source.get("suggested_commands", [])
            ],
            *[
                command
                for invariant in invariants
                for command in invariant.get("commands", [])
            ],
        ]
    )

    if auto_scanned and not source_reports:
        warnings.append("no content source files were found under known romhack content roots")

    return {
        "schema_version": 1,
        "kind": "unified_debugger_content_mirror",
        "root": str(root),
        "valid": not errors,
        "passed": not errors and not failed,
        "auto_scanned": auto_scanned,
        "requested_source_files": list(source_files),
        "changed_files": list(changed_files),
        "rom": rom_context.get("rom_path", ""),
        "symbols_path": rom_context.get("symbols_path", ""),
        "rom_available": bool(rom_context.get("available")),
        "source_file_count": len(source_reports),
        "invariant_count": len(invariants),
        "passed_invariant_count": len(passed),
        "failed_invariant_count": len(failed),
        "warning_invariant_count": len(warning_invariants),
        "rom_mirror_count": len(rom_mirrors),
        "passed_rom_mirror_count": len(passed_rom_mirrors),
        "failed_rom_mirror_count": len(failed_rom_mirrors),
        "warning_rom_mirror_count": len(warning_rom_mirrors),
        "error_count": len(unique_list(errors)),
        "warning_count": len(unique_list(warnings)),
        "errors": unique_list(errors),
        "warnings": unique_list(warnings),
        "source_files": source_reports,
        "invariants": invariants,
        "rom_mirrors": rom_mirrors,
        "failed_invariants": failed,
        "commands": commands,
        "runnable_commands": [command for command in commands if command_is_runnable(command)],
        "blocked_commands": [command for command in commands if not command_is_runnable(command)],
        "known_limits": [
            "This is a Pokemon Gold romhack content mirror over RGBDS source structure; it is not a dynamic emulator replay.",
            "Map event tables, common script-command bytecode, text macro blocks, movement data streams, audio channel headers, labeled db/dw/dn data blocks, and labeled/aggregate INCBIN assets are byte-compared against the built ROM when ROM and symbols are available.",
        ],
    }


def analyze_source_file(raw_path: str, *, root: Path, rom_context: dict[str, Any] | None = None) -> dict[str, Any]:
    path = resolve_path(raw_path, root=root)
    normalized = display_path(path, root=root)
    commands = source_commands(normalized)
    errors: list[str] = []
    warnings: list[str] = []
    invariants: list[dict[str, Any]] = []

    if not path.exists() or path.is_dir():
        message = f"missing source file: {raw_path}"
        errors.append(message)
        invariants.append(
            content_invariant(
                invariant_id=f"{normalized}:source_exists",
                invariant_type="source_exists",
                status="failed",
                severity=85,
                title=f"Source file is missing: {normalized}",
                source_file=normalized,
                evidence=[message],
                commands=[f"python -m tools.debugger ingest --changed-file {normalized}"],
                related_files=[normalized],
            )
        )
        return _empty_source_report(normalized, exists=False, errors=errors, warnings=warnings, invariants=invariants, commands=commands)

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        message = f"could not read source file {raw_path}: {exc}"
        errors.append(message)
        invariants.append(
            content_invariant(
                invariant_id=f"{normalized}:source_readable",
                invariant_type="source_readable",
                status="failed",
                severity=85,
                title=f"Source file could not be read: {normalized}",
                source_file=normalized,
                evidence=[message],
                commands=[f"python -m tools.debugger ingest --changed-file {normalized}"],
                related_files=[normalized],
            )
        )
        return _empty_source_report(normalized, exists=True, errors=errors, warnings=warnings, invariants=invariants, commands=commands)

    parsed = parse_rgbds_source(text, source_file=normalized, root=root)
    invariants.append(
        content_invariant(
            invariant_id=f"{normalized}:source_exists",
            invariant_type="source_exists",
            status="passed",
            severity=0,
            title=f"Source file is readable: {normalized}",
            source_file=normalized,
            evidence=[f"bytes={len(text.encode('utf-8', errors='replace'))}"],
            commands=commands[:2],
            related_files=[normalized],
        )
    )
    invariants.extend(map_event_invariants(parsed, source_file=normalized))
    invariants.extend(map_event_rom_mirror_invariants(parsed, text, source_file=normalized, rom_context=rom_context or {}))
    invariants.extend(asset_invariants(parsed, root=root, source_file=normalized))
    invariants.extend(asset_rom_mirror_invariants(parsed, root=root, source_file=normalized, rom_context=rom_context or {}))
    invariants.extend(asset_table_rom_mirror_invariants(parsed, root=root, source_file=normalized, rom_context=rom_context or {}))
    invariants.extend(audio_channel_invariants(parsed, source_file=normalized))
    invariants.extend(audio_channel_rom_mirror_invariants(parsed, source_file=normalized, rom_context=rom_context or {}))
    invariants.extend(data_block_rom_mirror_invariants(parsed, source_file=normalized, rom_context=rom_context or {}))
    invariants.extend(script_command_rom_mirror_invariants(parsed, source_file=normalized, rom_context=rom_context or {}))
    invariants.extend(text_block_rom_mirror_invariants(parsed, source_file=normalized, rom_context=rom_context or {}))
    invariants.extend(movement_data_rom_mirror_invariants(parsed, source_file=normalized, rom_context=rom_context or {}))
    invariants.extend(object_constant_invariants(parsed, source_file=normalized))
    warnings.extend(parsed.get("warnings", []))

    return {
        "path": normalized,
        "exists": True,
        "errors": errors,
        "warnings": warnings,
        "line_count": parsed["line_count"],
        "label_count": len(parsed["labels"]),
        "global_label_count": len(parsed["global_labels"]),
        "labels": parsed["labels"][:40],
        "global_labels": parsed["global_labels"],
        "macro_counts": parsed["macro_counts"],
        "map_event_counts": {
            macro: parsed["macro_counts"].get(macro, 0)
            for macro in sorted(MAP_SECTION_MACROS)
        },
        "asset_count": len(parsed["assets"]),
        "assets": parsed["assets"][:40],
        "incbin_tables": parsed["incbin_tables"][:40],
        "data_block_count": len(parsed["data_blocks"]),
        "data_blocks": parsed["data_blocks"][:40],
        "script_block_count": len(parsed["script_blocks"]),
        "script_blocks": parsed["script_blocks"][:40],
        "text_block_count": len(parsed["text_blocks"]),
        "text_blocks": parsed["text_blocks"][:40],
        "movement_block_count": len(parsed["movement_blocks"]),
        "movement_blocks": parsed["movement_blocks"][:40],
        "channel_blocks": parsed["channel_blocks"][:40],
        "invariants": invariants,
        "rom_mirrors": [item for item in invariants if is_rom_mirror_invariant(item)],
        "rom_mirror_count": len([item for item in invariants if is_rom_mirror_invariant(item)]),
        "suggested_commands": commands,
    }


def _empty_source_report(
    normalized: str,
    *,
    exists: bool,
    errors: list[str],
    warnings: list[str],
    invariants: list[dict[str, Any]],
    commands: list[str],
) -> dict[str, Any]:
    return {
        "path": normalized,
        "exists": exists,
        "errors": errors,
        "warnings": warnings,
        "labels": [],
        "global_labels": [],
        "macro_counts": {},
        "assets": [],
        "data_blocks": [],
        "script_blocks": [],
        "text_blocks": [],
        "movement_blocks": [],
        "channel_blocks": [],
        "invariants": invariants,
        "suggested_commands": commands,
    }


def parse_rgbds_source(text: str, *, source_file: str, root: Path) -> dict[str, Any]:
    labels: list[dict[str, Any]] = []
    global_labels: list[dict[str, Any]] = []
    macro_lines: dict[str, list[int]] = {}
    assets: list[dict[str, Any]] = []
    incbin_tables: list[dict[str, Any]] = []
    warnings: list[str] = []
    lines = text.splitlines()
    current_global_label = ""
    pending_label = ""
    equs_macros: dict[str, str] = {}
    current_incbin_table: dict[str, Any] | None = None
    data_blocks: list[dict[str, Any]] = []
    current_data_block: dict[str, Any] | None = None

    def finish_data_block() -> None:
        nonlocal current_data_block
        if current_data_block and current_data_block.get("directives"):
            data_blocks.append(current_data_block)
        current_data_block = None

    for index, raw_line in enumerate(lines, start=1):
        clean = strip_comment(raw_line).rstrip()
        if not clean.strip():
            continue
        label, code = split_label(clean)
        effective_label = ""
        if label:
            effective_label = symbol_name_for_label(label, current_global_label=current_global_label)
            if not label.startswith("."):
                if current_incbin_table:
                    incbin_tables.append(current_incbin_table)
                finish_data_block()
                current_incbin_table = {
                    "label": effective_label,
                    "line": index,
                    "assets": [],
                    "eligible": True,
                    "blockers": [],
                }
                current_data_block = {
                    "label": effective_label,
                    "line": index,
                    "directives": [],
                }
            label_item = {
                "label": label,
                "line": index,
                "global": not label.startswith("."),
            }
            labels.append(label_item)
            if not label.startswith("."):
                global_labels.append(label_item)
                current_global_label = label
            pending_label = effective_label if not code else ""
        token = first_token(code)
        if token:
            macro_lines.setdefault(token, []).append(index)
        data_continuation = (
            current_data_block is not None
            and token in DATA_STRING_CONTINUATION_DIRECTIVES
            and bool(current_data_block.get("directives"))
        )
        if current_data_block is not None and (token in DATA_BYTE_DIRECTIVES or data_continuation):
            current_data_block["directives"].append(
                {
                    "directive": token,
                    "line": index,
                    "args": split_macro_args(code[len(token):]),
                }
            )
        elif current_data_block is not None and token and token not in ALLOWED_DATA_BLOCK_DIRECTIVES:
            finish_data_block()
        equs_match = DEF_EQUS_RE.match(code)
        if equs_match:
            equs_macros[equs_match.group("name")] = equs_match.group("value")
        incbin_entries = parse_incbin_entries(code, equs_macros=equs_macros)
        if incbin_entries:
            rom_label = effective_label or pending_label
        else:
            rom_label = ""
        for incbin in incbin_entries:
            asset_path = str(incbin["path"])
            asset_abs = resolve_path(asset_path, root=root)
            assets.append(
                {
                    "path": asset_path,
                    "line": index,
                    "rom_label": rom_label,
                    "incbin_args": incbin.get("args", []),
                    "exists": asset_abs.exists() and asset_abs.is_file(),
                    "display_path": display_path(asset_abs, root=root),
                }
            )
            if current_incbin_table is not None:
                current_incbin_table["assets"].append(
                    {
                        "path": asset_path,
                        "line": index,
                        "incbin_args": incbin.get("args", []),
                    }
                )
        if incbin_entries:
            pending_label = ""
        elif current_incbin_table is not None and token and token not in ALLOWED_INCBIN_TABLE_DIRECTIVES:
            current_incbin_table["eligible"] = False
            current_incbin_table["blockers"].append(f"{index}:{token}")
        elif token or (label and code):
            pending_label = ""
    if current_incbin_table:
        incbin_tables.append(current_incbin_table)
    finish_data_block()

    source_constants = parse_source_constants(lines)

    return {
        "source_file": source_file,
        "line_count": len(lines),
        "labels": labels,
        "global_labels": global_labels,
        "constants": source_constants,
        "macro_lines": macro_lines,
        "macro_counts": {name: len(line_numbers) for name, line_numbers in sorted(macro_lines.items())},
        "assets": assets,
        "incbin_tables": [
            table
            for table in incbin_tables
            if len(table.get("assets", [])) > 1
        ],
        "data_blocks": data_blocks,
        "script_blocks": parse_script_blocks(lines),
        "text_blocks": parse_text_blocks(lines),
        "movement_blocks": parse_movement_blocks(lines),
        "channel_blocks": parse_channel_blocks(lines),
        "object_const_count": count_object_constants(lines),
        "warnings": warnings,
    }


def duplicate_label_invariants(label_occurrences: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    out = []
    for label, occurrences in sorted(label_occurrences.items()):
        if len(occurrences) < 2:
            continue
        evidence = [
            f"{item['source_file']}:{item['line']}"
            for item in occurrences
        ]
        source_file = str(occurrences[0]["source_file"])
        out.append(
            content_invariant(
                invariant_id=f"global_label_unique:{label}",
                invariant_type="global_label_unique",
                status="failed",
                severity=82,
                title=f"Duplicate global RGBDS label: {label}",
                source_file=source_file,
                line=int(occurrences[0]["line"]),
                evidence=evidence,
                commands=[
                    f"python -m tools.debugger provenance --source-file {item['source_file']}"
                    for item in occurrences[:4]
                ],
                related_files=[str(item["source_file"]) for item in occurrences],
                related_symbols=[label],
            )
        )
    return out


def auto_content_sources(*, root: Path, max_files: int) -> list[str]:
    paths: list[Path] = []
    for prefix in CONTENT_ROOTS:
        directory = root / prefix
        if not directory.exists() or not directory.is_dir():
            continue
        paths.extend(sorted(directory.rglob("*.asm")))
        if len(paths) >= max_files:
            break
    return [display_path(path, root=root) for path in paths[:max_files]]


def is_rom_mirror_invariant(item: dict[str, Any]) -> bool:
    return str(item.get("type", "")) in ROM_MIRROR_INVARIANT_TYPES
