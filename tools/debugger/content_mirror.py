from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from .catalog import ROOT
from .provenance import display_path, resolve_path
from .workflow import command_is_runnable


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
MAP_SECTION_MACROS = {
    "warp_event": "def_warp_events",
    "coord_event": "def_coord_events",
    "bg_event": "def_bg_events",
    "object_event": "def_object_events",
}
MAP_SECTION_TITLES = {
    "def_warp_events": "warp events",
    "def_coord_events": "coord events",
    "def_bg_events": "background events",
    "def_object_events": "object events",
}
LABEL_RE = re.compile(r"^\s*(?P<label>[A-Za-z_.$][A-Za-z0-9_.$]*)(?P<scope>::|:)")
LOCAL_LABEL_ONLY_RE = re.compile(r"^\s*(?P<label>\.[A-Za-z_.$][A-Za-z0-9_.$]*)\s*$")
TOKEN_RE = re.compile(r"^\s*(?P<token>[A-Za-z_?][A-Za-z0-9_?]*)\b")
INCBIN_RE = re.compile(r"\bINCBIN\s+\"(?P<path>[^\"]+)\"")
INCBIN_ARGS_RE = re.compile(r"\bINCBIN\s+(?P<args>.+)$")
CHANNEL_COUNT_RE = re.compile(r"^channel_count\s+(?P<count>[$0-9A-Fa-fx]+)\b")
CHANNEL_RE = re.compile(r"^channel\s+(?P<channel>[$0-9A-Fa-fx]+)\s*,\s*(?P<label>[A-Za-z_.$][A-Za-z0-9_.$]*)")
CHARMAP_RE = re.compile(r'^\s*charmap\s+"(?P<token>(?:\\.|[^"])*)"\s*,\s*(?P<value>[^;\s]+)')
RGBDS_DECIMAL_FORMAT_RE = re.compile(r"\{d:(?P<expr>[^}]+)\}")
SYM_LABEL_RE = re.compile(r"^(?P<bank>[0-9A-Fa-f]{2}):(?P<addr>[0-9A-Fa-f]{4})\s+(?P<label>\S+)$")
SYM_CONSTANT_RE = re.compile(r"^(?P<value>[0-9A-Fa-f]{1,8})\s+(?P<label>[A-Za-z_.$][A-Za-z0-9_.$]*)$")
DEF_EQU_RE = re.compile(r"^DEF\s+(?P<name>[A-Za-z_.$][A-Za-z0-9_.$]*)\s+EQU\s+(?P<expr>.+)$")
DEF_ASSIGN_RE = re.compile(r"^DEF\s+(?P<name>[A-Za-z_.$][A-Za-z0-9_.$]*)\s*=\s*(?P<expr>.+)$")
DEF_EQUS_RE = re.compile(r"^DEF\s+(?P<name>[A-Za-z_.$][A-Za-z0-9_.$]*)\s+EQUS\s+\"(?P<value>[^\"]+)\"$")
DEFAULT_ROM_PATH = "pokegold.gbc"
DEFAULT_SYMBOLS_PATH = "pokegold.sym"
MAP_EVENT_ENTRY_SIZES = {
    "warp_event": 5,
    "coord_event": 8,
    "bg_event": 5,
    "object_event": 13,
}
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
ALLOWED_INCBIN_TABLE_DIRECTIVES = {"table_width", "assert_table_length", "assert_table_length_nopad"}
DATA_BYTE_DIRECTIVES = {"db", "dw", "dn"}
DATA_STRING_CONTINUATION_DIRECTIVES = {"next", "line", "page", "para", "cont"}
ALLOWED_DATA_BLOCK_DIRECTIVES = (
    DATA_BYTE_DIRECTIVES | DATA_STRING_CONTINUATION_DIRECTIVES | ALLOWED_INCBIN_TABLE_DIRECTIVES
)
SCRIPT_COMMAND_SPECS: dict[str, tuple[str, ...]] = {
    "scall": ("ptr",),
    "sjump": ("ptr",),
    "iffalse": ("ptr",),
    "iftrue": ("ptr",),
    "ifequal": ("u8", "ptr"),
    "ifnotequal": ("u8", "ptr"),
    "ifgreater": ("u8", "ptr"),
    "ifless": ("u8", "ptr"),
    "memjump": ("ptr",),
    "special": ("special",),
    "checkmapscene": ("map_id",),
    "setmapscene": ("map_id", "u8"),
    "checkscene": (),
    "setscene": ("u8",),
    "setval": ("u8",),
    "addval": ("u8",),
    "random": ("u8",),
    "checkver": (),
    "callasm": ("dba",),
    "readmem": ("ptr",),
    "writemem": ("ptr",),
    "loadvar": ("u8", "u8"),
    "checkitem": ("u8",),
    "giveitem": ("u8", "u8_default_1"),
    "takeitem": ("u8", "u8_default_1"),
    "givemoney": ("u8", "money24"),
    "takemoney": ("u8", "money24"),
    "checkmoney": ("u8", "money24"),
    "givecoins": ("u16",),
    "takecoins": ("u16",),
    "checkcoins": ("u16",),
    "checkevent": ("u16",),
    "clearevent": ("u16",),
    "setevent": ("u16",),
    "checkflag": ("u16",),
    "clearflag": ("u16",),
    "setflag": ("u16",),
    "xycompare": ("ptr",),
    "warpmod": ("u8", "map_id"),
    "blackoutmod": ("map_id",),
    "warp": ("map_id", "u8", "u8"),
    "loadmem": ("ptr", "u8"),
    "readvar": ("u8",),
    "writevar": ("u8",),
    "addcellnum": ("u8",),
    "delcellnum": ("u8",),
    "checkcellnum": ("u8",),
    "checktime": ("u8",),
    "checkpoke": ("u8",),
    "givepoke": ("givepoke",),
    "giveegg": ("u8", "u8"),
    "givepokemail": ("ptr",),
    "checkpokemail": ("ptr",),
    "getitemname": ("u8_arg_2", "u8_arg_1"),
    "gettrainername": ("trainername",),
    "getmoney": ("u8_arg_2", "u8_arg_1"),
    "getcoins": ("u8",),
    "getnum": ("u8",),
    "getmonname": ("u8_arg_2", "u8_arg_1"),
    "getcurlandmarkname": ("u8",),
    "getstring": ("ptr_arg_2", "u8_arg_1"),
    "itemnotify": (),
    "pocketisfull": (),
    "opentext": (),
    "reanchormap": ("u8_default_0",),
    "closetext": (),
    "writetext": ("ptr",),
    "yesorno": (),
    "loadmenu": ("ptr",),
    "closewindow": (),
    "pokepic": ("u8",),
    "closepokepic": (),
    "_2dmenu": (),
    "jumptextfaceplayer": ("ptr",),
    "jumptext": ("ptr",),
    "waitbutton": (),
    "promptbutton": (),
    "applymovement": ("u8", "ptr"),
    "applymovementlasttalked": ("ptr",),
    "faceplayer": (),
    "setlasttalked": ("u8",),
    "showemote": ("u8", "u8", "u8"),
    "turnobject": ("u8", "u8"),
    "faceobject": ("u8", "u8"),
    "variablesprite": ("u8_minus_sprite_vars", "u8"),
    "appear": ("u8",),
    "disappear": ("u8",),
    "follow": ("u8", "u8"),
    "stopfollow": (),
    "moveobject": ("u8", "u8", "u8"),
    "writeobjectxy": ("u8",),
    "loademote": ("u8",),
    "follownotexact": ("u8", "u8"),
    "verticalmenu": (),
    "loadtrainer": ("u8", "u8"),
    "startbattle": (),
    "reloadmapafterbattle": (),
    "scripttalkafter": (),
    "endifjustbattled": (),
    "checkjustbattled": (),
    "winlosstext": ("ptr", "ptr"),
    "earthquake": ("u8",),
    "changeblock": ("u8", "u8", "u8"),
    "reloadmap": (),
    "refreshmap": (),
    "delcmdqueue": ("u8",),
    "writecmdqueue": ("ptr",),
    "loadwildmon": ("u8", "u8"),
    "loadtemptrainer": ("u8", "u8"),
    "randomwildmon": (),
    "catchtutorial": ("u8",),
    "newloadmap": ("u8",),
    "cry": ("u16",),
    "playmusic": ("u16",),
    "musicfadeout": ("u16", "u8"),
    "playmapmusic": (),
    "dontrestartmapmusic": (),
    "pause": ("u8",),
    "playsound": ("u16",),
    "waitsfx": (),
    "warpsound": (),
    "specialsound": (),
    "autoinput": ("dba",),
    "jumpstd": ("stdscript",),
    "callstd": ("stdscript",),
    "endcallback": (),
    "end": (),
    "reloadend": ("u8",),
    "endall": (),
    "verbosegiveitem": ("u8", "u8_default_1"),
    "pokemart": ("u8", "u16"),
    "elevator": ("ptr",),
    "trade": ("u8",),
    "askforphonenumber": ("u8",),
    "phonecall": ("ptr",),
    "hangup": (),
    "describedecoration": ("u8",),
    "fruittree": ("u8",),
    "specialphonecall": ("u16",),
    "checkphonecall": (),
    "swarm": ("map_id",),
    "halloffame": (),
    "credits": (),
    "sdefer": ("ptr",),
    "warpcheck": (),
    "stopandsjump": ("ptr",),
}
SCRIPT_DATA_MACRO_SPECS: dict[str, tuple[str, ...]] = {
    "cmdqueue": (),
    "stonetable": (),
    "trainer": (),
    "doorstate": (),
}
SCRIPT_TERMINAL_COMMANDS = {"sjump", "jumpstd", "jumptext", "jumptextfaceplayer", "end", "endcallback", "endall"}
TEXT_LINE_MACROS = {
    "text": "TX_START",
    "next": "<NEXT>",
    "line": "<LINE>",
    "page": "@",
    "para": "<PARA>",
    "cont": "<CONT>",
}
TEXT_TERMINATOR_MACROS = {
    "done": "<DONE>",
    "prompt": "<PROMPT>",
}
TEXT_COMMAND_SPECS: dict[str, tuple[str, ...]] = {
    "text_start": ("const:TX_START",),
    "text_ram": ("const:TX_RAM", "ptr"),
    "text_bcd": ("const:TX_BCD", "ptr", "u8"),
    "text_move": ("const:TX_MOVE", "ptr"),
    "text_end": ("const:TX_END",),
    "text_promptbutton": ("const:TX_PROMPT_BUTTON",),
    "text_waitbutton": ("const:TX_WAIT_BUTTON",),
    "text_scroll": ("const:TX_SCROLL",),
    "text_pause": ("const:TX_PAUSE",),
    "text_dots": ("const:TX_DOTS", "u8"),
    "text_buffer": ("const:TX_STRINGBUFFER", "u8"),
    "text_today": ("const:TX_DAY",),
}
NON_SCRIPT_BLOCK_START_TOKENS = (
    DATA_BYTE_DIRECTIVES
    | set(MAP_SECTION_MACROS)
    | set(MAP_SECTION_MACROS.values())
    | set(TEXT_LINE_MACROS)
    | set(TEXT_TERMINATOR_MACROS)
    | set(TEXT_COMMAND_SPECS)
    | {
        "INCBIN",
        "MACRO",
        "ENDM",
        "SECTION",
        "rept",
        "endr",
        "object_const_def",
        "def_scene_scripts",
        "scene_script",
        "def_callbacks",
        "callback",
        "conditional_event",
        "itemball",
        "hiddenitem",
        "tmhm",
        "dbw",
        "bigdw",
        "bigdt",
        "farcall",
        "call",
        "ret",
        "reti",
        "jp",
        "jr",
        "ld",
        "ldi",
        "ldd",
        "cp",
        "inc",
        "dec",
        "push",
        "pop",
        "xor",
        "and",
        "or",
        "add",
        "adc",
        "sub",
        "sbc",
        "rst",
        "bit",
        "set",
        "res",
    }
)
MOVEMENT_DIRECTIONAL_MACROS = {
    "turn_head": "movement_turn_head",
    "turn_step": "movement_turn_step",
    "slow_step": "movement_slow_step",
    "step": "movement_step",
    "big_step": "movement_big_step",
    "slow_slide_step": "movement_slow_slide_step",
    "slide_step": "movement_slide_step",
    "fast_slide_step": "movement_fast_slide_step",
    "turn_away": "movement_turn_away",
    "turn_in": "movement_turn_in",
    "turn_waterfall": "movement_turn_waterfall",
    "slow_jump_step": "movement_slow_jump_step",
    "jump_step": "movement_jump_step",
    "fast_jump_step": "movement_fast_jump_step",
}
MOVEMENT_NO_ARG_MACROS = {
    "remove_sliding": "movement_remove_sliding",
    "set_sliding": "movement_set_sliding",
    "remove_fixed_facing": "movement_remove_fixed_facing",
    "fix_facing": "movement_fix_facing",
    "show_object": "movement_show_object",
    "hide_object": "movement_hide_object",
    "step_end": "movement_step_end",
    "remove_object": "movement_remove_object",
    "step_loop": "movement_step_loop",
    "step_stop": "movement_step_stop",
    "teleport_from": "movement_teleport_from",
    "teleport_to": "movement_teleport_to",
    "skyfall": "movement_skyfall",
    "step_bump": "movement_step_bump",
    "fish_got_bite": "movement_fish_got_bite",
    "fish_cast_rod": "movement_fish_cast_rod",
    "hide_emote": "movement_hide_emote",
    "show_emote": "movement_show_emote",
    "tree_shake": "movement_tree_shake",
}
MOVEMENT_U8_ARG_MACROS = {
    "step_wait_end": "movement_step_wait_end",
    "step_dig": "movement_step_dig",
    "step_shake": "movement_step_shake",
    "rock_smash": "movement_rock_smash",
    "return_dig": "movement_return_dig",
}
MOVEMENT_SPECIAL_MACROS = {"step_sleep"}


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
        return {
            "path": normalized,
            "exists": False,
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
        return {
            "path": normalized,
            "exists": True,
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


def map_event_invariants(parsed: dict[str, Any], *, source_file: str) -> list[dict[str, Any]]:
    macro_lines = parsed["macro_lines"]
    is_map_file = is_map_event_file(source_file, parsed)
    if not is_map_file:
        return []

    out: list[dict[str, Any]] = []
    has_map_events_label = any(
        str(label["label"]).endswith("_MapEvents")
        for label in parsed["global_labels"]
    )
    map_event_macro_count = sum(
        len(macro_lines.get(name, []))
        for name in [*MAP_SECTION_MACROS, *MAP_SECTION_MACROS.values()]
    )
    out.append(
        content_invariant(
            invariant_id=f"{source_file}:map_events_label",
            invariant_type="map_events_label",
            status="passed" if has_map_events_label else "failed",
            severity=72,
            title=(
                f"{source_file} declares a _MapEvents label"
                if has_map_events_label
                else f"{source_file} uses map-event macros without a _MapEvents label"
            ),
            source_file=source_file,
            evidence=[f"map_event_macro_count={map_event_macro_count}"],
            commands=source_commands(source_file),
            related_files=[source_file],
        )
    )

    for event_macro, section_macro in MAP_SECTION_MACROS.items():
        event_lines = macro_lines.get(event_macro, [])
        section_lines = macro_lines.get(section_macro, [])
        title = MAP_SECTION_TITLES[section_macro]
        section_present = bool(section_lines)
        out.append(
            content_invariant(
                invariant_id=f"{source_file}:map_{event_macro}_section",
                invariant_type="map_event_section",
                status="passed" if section_present else "failed",
                severity=70,
                title=(
                    f"{source_file} declares {title}"
                    if section_present
                    else f"{source_file} is missing {section_macro} for {title}"
                ),
                source_file=source_file,
                line=section_lines[0] if section_lines else 0,
                evidence=[
                    f"{event_macro}_count={len(event_lines)}",
                    f"{section_macro}_count={len(section_lines)}",
                ],
                commands=[
                    f"python -m tools.debugger expect --source-file {source_file} --expect contains={section_macro}",
                    *source_commands(source_file),
                ],
                related_files=[source_file],
            )
        )
        if not event_lines or not section_lines:
            continue
        ordered = min(event_lines) > min(section_lines)
        out.append(
            content_invariant(
                invariant_id=f"{source_file}:map_{event_macro}_order",
                invariant_type="map_event_order",
                status="passed" if ordered else "failed",
                severity=70,
                title=(
                    f"{event_macro} entries follow {section_macro}"
                    if ordered
                    else f"{event_macro} entries appear before {section_macro}"
                ),
                source_file=source_file,
                line=min(event_lines),
                evidence=[
                    f"first_{section_macro}_line={min(section_lines)}",
                    f"first_{event_macro}_line={min(event_lines)}",
                ],
                commands=[
                    f"python -m tools.debugger expect --source-file {source_file} --expect contains={event_macro}",
                    *source_commands(source_file),
                ],
                related_files=[source_file],
            )
        )
    return out


def asset_invariants(parsed: dict[str, Any], *, root: Path, source_file: str) -> list[dict[str, Any]]:
    out = []
    for asset in parsed["assets"]:
        asset_path = str(asset["path"])
        exists = bool(asset["exists"])
        related = [source_file, str(asset.get("display_path") or asset_path)]
        out.append(
            content_invariant(
                invariant_id=f"{source_file}:incbin_asset_exists:{asset_path}",
                invariant_type="incbin_asset_exists",
                status="passed" if exists else "failed",
                severity=78,
                title=(
                    f"INCBIN asset exists: {asset_path}"
                    if exists
                    else f"Missing INCBIN asset: {asset_path}"
                ),
                source_file=source_file,
                line=int(asset["line"]),
                evidence=[f"asset={asset_path}", f"resolved={resolve_path(asset_path, root=root)}"],
                commands=[
                    f"python -m tools.debugger content-mirror --source-file {source_file}",
                    f"python -m tools.debugger gate --changed-file {source_file}",
                    f"python -m tools.debugger provenance --source-file {source_file}",
                ],
                related_files=related,
            )
        )
    return out


def asset_rom_mirror_invariants(
    parsed: dict[str, Any],
    *,
    root: Path,
    source_file: str,
    rom_context: dict[str, Any],
) -> list[dict[str, Any]]:
    if not rom_context.get("available"):
        return []
    out: list[dict[str, Any]] = []
    for asset in parsed["assets"]:
        asset_path = str(asset.get("path", ""))
        rom_label = str(asset.get("rom_label", ""))
        if not asset_path or not rom_label:
            continue
        commands = [
            f"python -m tools.debugger content-mirror --source-file {source_file}",
            f"python -m tools.debugger provenance --source-file {source_file}",
            f"python -m tools.debugger compare --changed-file {source_file}",
        ]
        symbol = rom_context.get("labels", {}).get(rom_label)
        related_files = [source_file, asset_path, str(rom_context.get("rom_path", "")), str(rom_context.get("symbols_path", ""))]
        if not symbol:
            out.append(
                content_invariant(
                    invariant_id=f"{source_file}:incbin_asset_rom_bytes:{asset_path}:{asset.get('line', 0)}",
                    invariant_type="incbin_asset_rom_bytes",
                    status="warning",
                    severity=52,
                    title=f"INCBIN label is missing from built ROM symbols: {rom_label}",
                    source_file=source_file,
                    line=int(asset.get("line", 0)),
                    evidence=[
                        f"asset={asset_path}",
                        f"label={rom_label}",
                        f"symbols={rom_context.get('symbols_path', '')}",
                    ],
                    commands=commands,
                    related_files=related_files,
                    related_symbols=[rom_label],
                )
            )
            continue

        payload = load_incbin_payload(asset, root=root, constants=rom_context.get("constants", {}))
        if payload["errors"]:
            out.append(
                content_invariant(
                    invariant_id=f"{source_file}:incbin_asset_rom_bytes:{asset_path}:{asset.get('line', 0)}",
                    invariant_type="incbin_asset_rom_bytes",
                    status="warning",
                    severity=48,
                    title=f"INCBIN asset could not be encoded for ROM byte comparison: {asset_path}",
                    source_file=source_file,
                    line=int(asset.get("line", 0)),
                    evidence=[
                        f"asset={asset_path}",
                        f"label={rom_label}",
                        *payload["errors"][:8],
                    ],
                    commands=commands,
                    related_files=related_files,
                    related_symbols=[rom_label],
                )
            )
            continue

        expected = bytes(payload["bytes"])
        rom_bytes = rom_context.get("rom_bytes", b"")
        offset = int(symbol["rom_offset"])
        actual = rom_bytes[offset:offset + len(expected)]
        short_read = len(actual) != len(expected)
        mismatch_index = first_mismatch(expected, actual) if not short_read else min(len(actual), max(0, len(expected) - 1))
        matched = not short_read and mismatch_index < 0
        evidence = [
            f"asset={asset_path}",
            f"label={rom_label}",
            f"bank=${int(symbol['bank']):02x}",
            f"address=${int(symbol['address']):04x}",
            f"rom_offset=${offset:06x}",
            f"asset_offset={payload['asset_offset']}",
            f"expected_len={len(expected)}",
            f"actual_len={len(actual)}",
            f"expected_sha256={hashlib.sha256(expected).hexdigest()}",
            f"actual_sha256={hashlib.sha256(actual).hexdigest()}",
        ]
        if mismatch_index >= 0:
            expected_byte = expected[mismatch_index] if mismatch_index < len(expected) else None
            actual_byte = actual[mismatch_index] if mismatch_index < len(actual) else None
            evidence.append(
                "first_mismatch="
                f"{mismatch_index} expected={format_optional_byte(expected_byte)} actual={format_optional_byte(actual_byte)}"
            )
            evidence.append(f"expected_window={hex_window(expected, mismatch_index)}")
            evidence.append(f"actual_window={hex_window(actual, mismatch_index)}")
        out.append(
            content_invariant(
                invariant_id=f"{source_file}:incbin_asset_rom_bytes:{asset_path}:{asset.get('line', 0)}",
                invariant_type="incbin_asset_rom_bytes",
                status="passed" if matched else "failed",
                severity=0 if matched else 88,
                title=(
                    f"INCBIN asset ROM bytes match source asset: {asset_path}"
                    if matched
                    else f"INCBIN asset ROM bytes differ from source asset: {asset_path}"
                ),
                source_file=source_file,
                line=int(asset.get("line", 0)),
                evidence=evidence,
                commands=commands,
                related_files=related_files,
                related_symbols=[rom_label],
            )
        )
    return out


def asset_table_rom_mirror_invariants(
    parsed: dict[str, Any],
    *,
    root: Path,
    source_file: str,
    rom_context: dict[str, Any],
) -> list[dict[str, Any]]:
    if not rom_context.get("available"):
        return []
    out: list[dict[str, Any]] = []
    for table in parsed.get("incbin_tables", []):
        label = str(table.get("label", ""))
        assets = [item for item in table.get("assets", []) if isinstance(item, dict)]
        if not label or len(assets) < 2:
            continue
        commands = [
            f"python -m tools.debugger content-mirror --source-file {source_file}",
            f"python -m tools.debugger provenance --source-file {source_file}",
            f"python -m tools.debugger compare --changed-file {source_file}",
        ]
        related_files = [
            source_file,
            *unique_list(str(asset.get("path", "")) for asset in assets[:12]),
            str(rom_context.get("rom_path", "")),
            str(rom_context.get("symbols_path", "")),
        ]
        if not bool(table.get("eligible", False)):
            continue
        symbol = rom_context.get("labels", {}).get(label)
        if not symbol:
            out.append(
                content_invariant(
                    invariant_id=f"{source_file}:incbin_table_rom_bytes:{label}",
                    invariant_type="incbin_table_rom_bytes",
                    status="warning",
                    severity=50,
                    title=f"INCBIN table label is missing from built ROM symbols: {label}",
                    source_file=source_file,
                    line=int(table.get("line", 0)),
                    evidence=[
                        f"label={label}",
                        f"asset_count={len(assets)}",
                        f"symbols={rom_context.get('symbols_path', '')}",
                    ],
                    commands=commands,
                    related_files=related_files,
                    related_symbols=[label],
                )
            )
            continue
        payload = load_incbin_table_payload(assets, root=root, constants=rom_context.get("constants", {}))
        if payload["errors"]:
            out.append(
                content_invariant(
                    invariant_id=f"{source_file}:incbin_table_rom_bytes:{label}",
                    invariant_type="incbin_table_rom_bytes",
                    status="warning",
                    severity=48,
                    title=f"INCBIN table could not be encoded for ROM byte comparison: {label}",
                    source_file=source_file,
                    line=int(table.get("line", 0)),
                    evidence=[
                        f"label={label}",
                        f"asset_count={len(assets)}",
                        *payload["errors"][:8],
                    ],
                    commands=commands,
                    related_files=related_files,
                    related_symbols=[label],
                )
            )
            continue
        expected = bytes(payload["bytes"])
        rom_bytes = rom_context.get("rom_bytes", b"")
        offset = int(symbol["rom_offset"])
        actual = rom_bytes[offset:offset + len(expected)]
        short_read = len(actual) != len(expected)
        mismatch_index = first_mismatch(expected, actual) if not short_read else min(len(actual), max(0, len(expected) - 1))
        matched = not short_read and mismatch_index < 0
        evidence = [
            f"label={label}",
            f"asset_count={len(assets)}",
            f"bank=${int(symbol['bank']):02x}",
            f"address=${int(symbol['address']):04x}",
            f"rom_offset=${offset:06x}",
            f"expected_len={len(expected)}",
            f"actual_len={len(actual)}",
            f"expected_sha256={hashlib.sha256(expected).hexdigest()}",
            f"actual_sha256={hashlib.sha256(actual).hexdigest()}",
        ]
        if mismatch_index >= 0:
            expected_byte = expected[mismatch_index] if mismatch_index < len(expected) else None
            actual_byte = actual[mismatch_index] if mismatch_index < len(actual) else None
            evidence.append(
                "first_mismatch="
                f"{mismatch_index} expected={format_optional_byte(expected_byte)} actual={format_optional_byte(actual_byte)}"
            )
            evidence.append(f"expected_window={hex_window(expected, mismatch_index)}")
            evidence.append(f"actual_window={hex_window(actual, mismatch_index)}")
        out.append(
            content_invariant(
                invariant_id=f"{source_file}:incbin_table_rom_bytes:{label}",
                invariant_type="incbin_table_rom_bytes",
                status="passed" if matched else "failed",
                severity=0 if matched else 88,
                title=(
                    f"INCBIN table ROM bytes match source assets: {label}"
                    if matched
                    else f"INCBIN table ROM bytes differ from source assets: {label}"
                ),
                source_file=source_file,
                line=int(table.get("line", 0)),
                evidence=evidence,
                commands=commands,
                related_files=related_files,
                related_symbols=[label],
            )
        )
    return out


def load_incbin_payload(asset: dict[str, Any], *, root: Path, constants: dict[str, int]) -> dict[str, Any]:
    asset_path = str(asset.get("path", ""))
    path = resolve_path(asset_path, root=root)
    errors: list[str] = []
    if not path.exists() or not path.is_file():
        return {"bytes": b"", "asset_offset": 0, "errors": [f"missing_asset={asset_path}"]}
    args = [str(item).strip() for item in asset.get("incbin_args", [])]
    offset = 0
    length: int | None = None
    if len(args) >= 2:
        value = evaluate_int_expression(args[1], constants)
        if value is None:
            errors.append(f"unresolved_asset_offset={args[1]}")
        else:
            offset = value
    if len(args) >= 3:
        value = evaluate_int_expression(args[2], constants)
        if value is None:
            errors.append(f"unresolved_asset_length={args[2]}")
        else:
            length = value
    if len(args) > 3:
        errors.append(f"unsupported_incbin_arg_count={len(args)}")
    data = path.read_bytes()
    if offset < 0 or offset > len(data):
        errors.append(f"asset_offset_out_of_range={offset}")
        offset = max(0, min(offset, len(data)))
    if length is not None and length < 0:
        errors.append(f"asset_length_negative={length}")
        length = 0
    end = len(data) if length is None else min(len(data), offset + length)
    if length is not None and offset + length > len(data):
        errors.append(f"asset_length_out_of_range={length}")
    return {"bytes": data[offset:end], "asset_offset": offset, "errors": unique_list(errors)}


def load_incbin_table_payload(
    assets: list[dict[str, Any]],
    *,
    root: Path,
    constants: dict[str, int],
) -> dict[str, Any]:
    out = bytearray()
    errors: list[str] = []
    for index, asset in enumerate(assets, start=1):
        payload = load_incbin_payload(asset, root=root, constants=constants)
        for error in payload["errors"]:
            errors.append(f"asset_{index}:{error}")
        out.extend(payload["bytes"])
    return {"bytes": bytes(out), "errors": unique_list(errors)}


def audio_channel_invariants(parsed: dict[str, Any], *, source_file: str) -> list[dict[str, Any]]:
    out = []
    for index, block in enumerate(parsed["channel_blocks"], start=1):
        expected = int(block["expected"])
        actual = int(block["actual"])
        out.append(
            content_invariant(
                invariant_id=f"{source_file}:audio_channel_count:{block['line']}:{index}",
                invariant_type="audio_channel_count",
                status="passed" if expected == actual else "failed",
                severity=74,
                title=(
                    f"channel_count {expected} matches {actual} channel declarations"
                    if expected == actual
                    else f"channel_count {expected} does not match {actual} channel declarations"
                ),
                source_file=source_file,
                line=int(block["line"]),
                evidence=[f"expected={expected}", f"actual={actual}"],
                commands=[
                    f"python -m tools.debugger expect --source-file {source_file} --expect contains=channel_count",
                    *source_commands(source_file),
                ],
                related_files=[source_file],
            )
        )
    return out


def audio_channel_rom_mirror_invariants(
    parsed: dict[str, Any],
    *,
    source_file: str,
    rom_context: dict[str, Any],
) -> list[dict[str, Any]]:
    if not rom_context.get("available"):
        return []
    out = []
    for index, block in enumerate(parsed["channel_blocks"], start=1):
        label = str(block.get("label", ""))
        if not label:
            continue
        commands = [
            f"python -m tools.debugger content-mirror --source-file {source_file}",
            f"python -m tools.debugger provenance --source-file {source_file}",
            f"python -m tools.debugger compare --changed-file {source_file}",
        ]
        related_files = [
            source_file,
            str(rom_context.get("rom_path", "")),
            str(rom_context.get("symbols_path", "")),
        ]
        symbol = rom_context.get("labels", {}).get(label)
        if not symbol:
            out.append(
                content_invariant(
                    invariant_id=f"{source_file}:audio_channel_rom_bytes:{block.get('line', 0)}:{index}",
                    invariant_type="audio_channel_rom_bytes",
                    status="warning",
                    severity=52,
                    title=f"{label} audio channel header is missing from built ROM symbols",
                    source_file=source_file,
                    line=int(block.get("line", 0)),
                    evidence=[
                        f"label={label}",
                        f"symbols={rom_context.get('symbols_path', '')}",
                    ],
                    commands=commands,
                    related_files=related_files,
                    related_symbols=[label],
                )
            )
            continue
        encoded = encode_audio_channel_header(block, rom_context=rom_context)
        if encoded["errors"]:
            out.append(
                content_invariant(
                    invariant_id=f"{source_file}:audio_channel_rom_bytes:{block.get('line', 0)}:{index}",
                    invariant_type="audio_channel_rom_bytes",
                    status="warning",
                    severity=55,
                    title=f"{label} audio channel header could not be fully encoded for ROM byte comparison",
                    source_file=source_file,
                    line=int(block.get("line", 0)),
                    evidence=[
                        f"label={label}",
                        *encoded["errors"][:10],
                    ],
                    commands=commands,
                    related_files=related_files,
                    related_symbols=[label, *encoded["related_symbols"]],
                )
            )
            continue
        expected = bytes(encoded["bytes"])
        rom_bytes = rom_context.get("rom_bytes", b"")
        offset = int(symbol["rom_offset"])
        actual = rom_bytes[offset:offset + len(expected)]
        short_read = len(actual) != len(expected)
        mismatch_index = first_mismatch(expected, actual) if not short_read else min(len(actual), max(0, len(expected) - 1))
        matched = not short_read and mismatch_index < 0
        evidence = [
            f"label={label}",
            f"channel_count={block.get('expected', 0)}",
            f"channel_declarations={block.get('actual', 0)}",
            f"bank=${int(symbol['bank']):02x}",
            f"address=${int(symbol['address']):04x}",
            f"rom_offset=${offset:06x}",
            f"expected_len={len(expected)}",
            f"actual_len={len(actual)}",
            f"expected_sha256={hashlib.sha256(expected).hexdigest()}",
            f"actual_sha256={hashlib.sha256(actual).hexdigest()}",
        ]
        if mismatch_index >= 0:
            expected_byte = expected[mismatch_index] if mismatch_index < len(expected) else None
            actual_byte = actual[mismatch_index] if mismatch_index < len(actual) else None
            evidence.append(
                "first_mismatch="
                f"{mismatch_index} expected={format_optional_byte(expected_byte)} actual={format_optional_byte(actual_byte)}"
            )
            evidence.append(f"expected_window={hex_window(expected, mismatch_index)}")
            evidence.append(f"actual_window={hex_window(actual, mismatch_index)}")
        out.append(
            content_invariant(
                invariant_id=f"{source_file}:audio_channel_rom_bytes:{block.get('line', 0)}:{index}",
                invariant_type="audio_channel_rom_bytes",
                status="passed" if matched else "failed",
                severity=0 if matched else 88,
                title=(
                    f"{label} ROM bytes match source audio channel header"
                    if matched
                    else f"{label} ROM bytes differ from source audio channel header"
                ),
                source_file=source_file,
                line=int(block.get("line", 0)),
                evidence=evidence,
                commands=commands,
                related_files=related_files,
                related_symbols=[label, *encoded["related_symbols"]],
            )
        )
    return out


def encode_audio_channel_header(block: dict[str, Any], *, rom_context: dict[str, Any]) -> dict[str, Any]:
    out: list[int] = []
    errors: list[str] = []
    related_symbols: list[str] = []
    constants = rom_context.get("constants", {})
    labels = rom_context.get("labels", {})
    expected = int(block.get("expected", 0))
    first_channel_high = (max(0, expected - 1) << 2) & 0x0f
    for index, channel in enumerate(dict_items(block.get("channels"))):
        channel_text = str(channel.get("channel", ""))
        channel_id = evaluate_int_expression(channel_text, constants)
        if channel_id is None:
            errors.append(f"unresolved_channel_id={channel_text}")
            continue
        channel_label = str(channel.get("label", ""))
        symbol = labels.get(channel_label)
        if not symbol:
            errors.append(f"unresolved_channel_label={channel_label}")
            continue
        related_symbols.append(channel_label)
        high = first_channel_high if index == 0 else 0
        low = (int(channel_id) - 1) & 0x0f
        out.append(((high & 0x0f) << 4) | low)
        address = int(symbol["address"]) & 0xffff
        out.extend([address & 0xff, address >> 8])
    if not out and block.get("channels"):
        errors.append("no_audio_channel_header_bytes_encoded")
    return {
        "bytes": out,
        "errors": unique_list(errors),
        "related_symbols": unique_list(related_symbols),
    }


def data_block_rom_mirror_invariants(
    parsed: dict[str, Any],
    *,
    source_file: str,
    rom_context: dict[str, Any],
) -> list[dict[str, Any]]:
    if not rom_context.get("available"):
        return []
    out: list[dict[str, Any]] = []
    for index, block in enumerate(parsed.get("data_blocks", []), start=1):
        label = str(block.get("label", ""))
        if not label or label.endswith("_MapEvents"):
            continue
        commands = [
            f"python -m tools.debugger content-mirror --source-file {source_file}",
            f"python -m tools.debugger provenance --source-file {source_file}",
            f"python -m tools.debugger compare --changed-file {source_file}",
        ]
        related_files = [
            source_file,
            str(rom_context.get("rom_path", "")),
            str(rom_context.get("symbols_path", "")),
        ]
        symbol = rom_context.get("labels", {}).get(label)
        if not symbol:
            out.append(
                content_invariant(
                    invariant_id=f"{source_file}:labeled_data_rom_bytes:{label}",
                    invariant_type="labeled_data_rom_bytes",
                    status="warning",
                    severity=50,
                    title=f"{label} data block is missing from built ROM symbols",
                    source_file=source_file,
                    line=int(block.get("line", 0)),
                    evidence=[
                        f"label={label}",
                        f"symbols={rom_context.get('symbols_path', '')}",
                    ],
                    commands=commands,
                    related_files=related_files,
                    related_symbols=[label],
                )
            )
            continue
        encoded = encode_labeled_data_block(
            block,
            rom_context=rom_context,
            source_constants=parsed.get("constants", {}),
        )
        if encoded["errors"]:
            out.append(
                content_invariant(
                    invariant_id=f"{source_file}:labeled_data_rom_bytes:{label}",
                    invariant_type="labeled_data_rom_bytes",
                    status="warning",
                    severity=54,
                    title=f"{label} data block could not be fully encoded for ROM byte comparison",
                    source_file=source_file,
                    line=int(block.get("line", 0)),
                    evidence=[
                        f"label={label}",
                        f"directive_count={len(block.get('directives', []))}",
                        *encoded["errors"][:12],
                    ],
                    commands=commands,
                    related_files=related_files,
                    related_symbols=[label, *encoded["related_symbols"]],
                )
            )
            continue
        expected = bytes(encoded["bytes"])
        if not expected:
            continue
        rom_bytes = rom_context.get("rom_bytes", b"")
        offset = int(symbol["rom_offset"])
        actual = rom_bytes[offset:offset + len(expected)]
        short_read = len(actual) != len(expected)
        mismatch_index = first_mismatch(expected, actual) if not short_read else min(len(actual), max(0, len(expected) - 1))
        matched = not short_read and mismatch_index < 0
        evidence = [
            f"label={label}",
            f"directive_count={len(block.get('directives', []))}",
            f"bank=${int(symbol['bank']):02x}",
            f"address=${int(symbol['address']):04x}",
            f"rom_offset=${offset:06x}",
            f"expected_len={len(expected)}",
            f"actual_len={len(actual)}",
            f"expected_sha256={hashlib.sha256(expected).hexdigest()}",
            f"actual_sha256={hashlib.sha256(actual).hexdigest()}",
        ]
        if mismatch_index >= 0:
            expected_byte = expected[mismatch_index] if mismatch_index < len(expected) else None
            actual_byte = actual[mismatch_index] if mismatch_index < len(actual) else None
            evidence.append(
                "first_mismatch="
                f"{mismatch_index} expected={format_optional_byte(expected_byte)} actual={format_optional_byte(actual_byte)}"
            )
            evidence.append(f"expected_window={hex_window(expected, mismatch_index)}")
            evidence.append(f"actual_window={hex_window(actual, mismatch_index)}")
        out.append(
            content_invariant(
                invariant_id=f"{source_file}:labeled_data_rom_bytes:{label}",
                invariant_type="labeled_data_rom_bytes",
                status="passed" if matched else "failed",
                severity=0 if matched else 88,
                title=(
                    f"{label} ROM bytes match source data block"
                    if matched
                    else f"{label} ROM bytes differ from source data block"
                ),
                source_file=source_file,
                line=int(block.get("line", 0)),
                evidence=evidence,
                commands=commands,
                related_files=related_files,
                related_symbols=[label, *encoded["related_symbols"]],
            )
        )
    return out


def encode_labeled_data_block(
    block: dict[str, Any],
    *,
    rom_context: dict[str, Any],
    source_constants: dict[str, int] | None = None,
) -> dict[str, Any]:
    out: list[int] = []
    errors: list[str] = []
    related_symbols: list[str] = []
    constants = {**rom_context.get("constants", {}), **(source_constants or {})}
    labels = rom_context.get("labels", {})
    charmap = rom_context.get("charmap", {})
    block_label = str(block.get("label", ""))

    def resolve_numeric(arg: str) -> int | None:
        return evaluate_int_expression(arg, constants)

    def resolve_pointer(arg: str) -> int | None:
        value = resolve_numeric(arg)
        if value is not None:
            return value
        label = arg.strip()
        symbol = labels.get(label)
        if symbol is None and label.startswith(".") and block_label:
            label = f"{block_label}{label}"
            symbol = labels.get(label)
        if symbol is None:
            return None
        related_symbols.append(label)
        return int(symbol["address"])

    def append_u8(arg: str, *, line: int) -> None:
        text = arg.strip()
        if is_quoted_rgbds_string(text):
            if not isinstance(charmap, dict) or not charmap:
                errors.append(f"line_{line}:missing_charmap_for_db_string={text}")
                return
            expanded = expand_rgbds_string_formats(text[1:-1], constants=constants, errors=errors, line=line)
            out.extend(encode_charmap_string(expanded, charmap=charmap, errors=errors, line=line))
            return
        value = resolve_numeric(text)
        if value is None:
            errors.append(f"line_{line}:unresolved_db_value={text}")
            return
        out.append(value & 0xff)

    def append_u16(arg: str, *, line: int) -> None:
        text = arg.strip()
        value = resolve_pointer(text)
        if value is None:
            errors.append(f"line_{line}:unresolved_dw_value={text}")
            return
        value &= 0xffff
        out.extend([value & 0xff, value >> 8])

    def append_nibble_pair(high_arg: str, low_arg: str, *, line: int) -> None:
        high_text = high_arg.strip()
        low_text = low_arg.strip()
        high = resolve_numeric(high_text)
        low = resolve_numeric(low_text)
        if high is None or low is None:
            if high is None:
                errors.append(f"line_{line}:unresolved_dn_high={high_text}")
            if low is None:
                errors.append(f"line_{line}:unresolved_dn_low={low_text}")
            return
        out.append(((high & 0x0f) << 4) | (low & 0x0f))

    for directive in dict_items(block.get("directives")):
        name = str(directive.get("directive", ""))
        args = [str(arg) for arg in directive.get("args", [])]
        line = int(directive.get("line", 0))
        if name == "db":
            for arg in args:
                append_u8(arg, line=line)
            continue
        if name == "dw":
            for arg in args:
                append_u16(arg, line=line)
            continue
        if name == "dn":
            if len(args) % 2:
                errors.append(f"line_{line}:dn_odd_arg_count={len(args)}")
            for pair_index in range(0, len(args) - 1, 2):
                append_nibble_pair(args[pair_index], args[pair_index + 1], line=line)
            continue
        if name in DATA_STRING_CONTINUATION_DIRECTIVES:
            prefix = TEXT_LINE_MACROS[name]
            append_charmap_token(out, prefix, charmap=charmap, errors=errors, line=line)
            if len(args) != 1 or not is_quoted_rgbds_string(args[0]):
                errors.append(f"line_{line}:unsupported_data_string_args={','.join(args)}")
                continue
            expanded = expand_rgbds_string_formats(args[0][1:-1], constants=constants, errors=errors, line=line)
            out.extend(encode_charmap_string(expanded, charmap=charmap, errors=errors, line=line))
            continue
        errors.append(f"line_{line}:unsupported_data_directive={name}")

    if not out and block.get("directives"):
        errors.append("no_data_block_bytes_encoded")
    return {
        "bytes": out,
        "errors": unique_list(errors),
        "related_symbols": unique_list(related_symbols),
    }


def is_quoted_rgbds_string(value: str) -> bool:
    text = value.strip()
    return len(text) >= 2 and text[0] == '"' and text[-1] == '"'


def script_command_rom_mirror_invariants(
    parsed: dict[str, Any],
    *,
    source_file: str,
    rom_context: dict[str, Any],
) -> list[dict[str, Any]]:
    if not rom_context.get("available"):
        return []
    out: list[dict[str, Any]] = []
    for index, block in enumerate(parsed.get("script_blocks", []), start=1):
        label = str(block.get("label", ""))
        if not label:
            continue
        commands = [
            f"python -m tools.debugger content-mirror --source-file {source_file}",
            f"python -m tools.debugger provenance --source-file {source_file}",
            f"python -m tools.debugger replay --changed-file {source_file} --scenario-id {label}",
            f"python -m tools.debugger compare --changed-file {source_file}",
        ]
        related_files = [
            source_file,
            str(rom_context.get("rom_path", "")),
            str(rom_context.get("symbols_path", "")),
        ]
        symbol = rom_context.get("labels", {}).get(label)
        if not symbol:
            out.append(
                content_invariant(
                    invariant_id=f"{source_file}:script_command_rom_bytes:{label}",
                    invariant_type="script_command_rom_bytes",
                    status="warning",
                    severity=50,
                    title=f"{label} script block is missing from built ROM symbols",
                    source_file=source_file,
                    line=int(block.get("line", 0)),
                    evidence=[
                        f"label={label}",
                        f"symbols={rom_context.get('symbols_path', '')}",
                    ],
                    commands=commands,
                    related_files=related_files,
                    related_symbols=[label],
                )
            )
            continue
        encoded = encode_script_command_block(
            block,
            rom_context=rom_context,
            source_constants=parsed.get("constants", {}),
        )
        if encoded["errors"]:
            out.append(
                content_invariant(
                    invariant_id=f"{source_file}:script_command_rom_bytes:{label}",
                    invariant_type="script_command_rom_bytes",
                    status="warning",
                    severity=58,
                    title=f"{label} script block could not be fully encoded for ROM byte comparison",
                    source_file=source_file,
                    line=int(block.get("line", 0)),
                    evidence=[
                        f"label={label}",
                        f"command_count={len(block.get('commands', []))}",
                        *encoded["errors"][:12],
                    ],
                    commands=commands,
                    related_files=related_files,
                    related_symbols=[label, *encoded["related_symbols"]],
                )
            )
            continue
        expected = bytes(encoded["bytes"])
        if not expected:
            continue
        rom_bytes = rom_context.get("rom_bytes", b"")
        offset = int(symbol["rom_offset"])
        actual = rom_bytes[offset:offset + len(expected)]
        short_read = len(actual) != len(expected)
        mismatch_index = first_mismatch(expected, actual) if not short_read else min(len(actual), max(0, len(expected) - 1))
        matched = not short_read and mismatch_index < 0
        evidence = [
            f"label={label}",
            f"command_count={len(block.get('commands', []))}",
            f"bank=${int(symbol['bank']):02x}",
            f"address=${int(symbol['address']):04x}",
            f"rom_offset=${offset:06x}",
            f"expected_len={len(expected)}",
            f"actual_len={len(actual)}",
            f"expected_sha256={hashlib.sha256(expected).hexdigest()}",
            f"actual_sha256={hashlib.sha256(actual).hexdigest()}",
        ]
        if mismatch_index >= 0:
            expected_byte = expected[mismatch_index] if mismatch_index < len(expected) else None
            actual_byte = actual[mismatch_index] if mismatch_index < len(actual) else None
            evidence.append(
                "first_mismatch="
                f"{mismatch_index} expected={format_optional_byte(expected_byte)} actual={format_optional_byte(actual_byte)}"
            )
            evidence.append(f"expected_window={hex_window(expected, mismatch_index)}")
            evidence.append(f"actual_window={hex_window(actual, mismatch_index)}")
        out.append(
            content_invariant(
                invariant_id=f"{source_file}:script_command_rom_bytes:{label}",
                invariant_type="script_command_rom_bytes",
                status="passed" if matched else "failed",
                severity=0 if matched else 90,
                title=(
                    f"{label} ROM bytes match source script command stream"
                    if matched
                    else f"{label} ROM bytes differ from source script command stream"
                ),
                source_file=source_file,
                line=int(block.get("line", 0)),
                evidence=evidence,
                commands=commands,
                related_files=related_files,
                related_symbols=[label, *encoded["related_symbols"]],
            )
        )
    return out


def encode_script_command_block(
    block: dict[str, Any],
    *,
    rom_context: dict[str, Any],
    source_constants: dict[str, int] | None = None,
) -> dict[str, Any]:
    out: list[int] = []
    errors: list[str] = []
    related_symbols: list[str] = []
    constants = {**rom_context.get("constants", {}), **(source_constants or {})}
    labels = rom_context.get("labels", {})
    block_label = str(block.get("label", ""))
    parent_label = str(block.get("parent_label", block_label))

    def command_opcode(name: str, *, line: int) -> int | None:
        value = constants.get(f"{name}_command")
        if value is None:
            errors.append(f"line_{line}:unresolved_script_command_opcode={name}_command")
            return None
        return int(value) & 0xff

    def argument(args: list[str], index: int, kind: str, *, line: int) -> str | None:
        if kind == "u8_default_1" and index >= len(args):
            return "1"
        if kind == "u8_default_0" and index >= len(args):
            return "0"
        if kind == "u8_arg_1":
            index = 0
        elif kind == "u8_arg_2":
            index = 1
        elif kind == "ptr_arg_2":
            index = 1
        if index >= len(args):
            errors.append(f"line_{line}:missing_script_arg_{index + 1}")
            return None
        return args[index]

    def resolve_numeric(arg: str) -> int | None:
        return evaluate_int_expression(arg, constants)

    def resolve_pointer(arg: str) -> int | None:
        value = resolve_numeric(arg)
        if value is not None:
            return value
        label = script_symbol_name(arg.strip(), block_label=parent_label)
        symbol = labels.get(label)
        if not symbol:
            return None
        related_symbols.append(label)
        return int(symbol["address"])

    def resolve_symbol(arg: str) -> tuple[str, dict[str, Any]] | None:
        label = script_symbol_name(arg.strip(), block_label=parent_label)
        symbol = labels.get(label)
        if not symbol:
            return None
        related_symbols.append(label)
        return label, symbol

    def append_u8(arg: str, *, line: int, field: str) -> None:
        value = resolve_numeric(arg)
        if value is None:
            errors.append(f"line_{line}:unresolved_{field}={arg}")
            return
        out.append(value & 0xff)

    def append_u16(arg: str, *, line: int, field: str) -> None:
        value = resolve_numeric(arg)
        if value is None:
            errors.append(f"line_{line}:unresolved_{field}={arg}")
            return
        value &= 0xffff
        out.extend([value & 0xff, value >> 8])

    def append_money24(arg: str, *, line: int, field: str) -> None:
        value = resolve_numeric(arg)
        if value is None:
            errors.append(f"line_{line}:unresolved_{field}={arg}")
            return
        value &= 0xffffff
        out.extend([(value >> 16) & 0xff, (value >> 8) & 0xff, value & 0xff])

    def append_pointer(arg: str, *, line: int, field: str) -> None:
        value = resolve_pointer(arg)
        if value is None:
            errors.append(f"line_{line}:unresolved_{field}_label={arg}")
            return
        value &= 0xffff
        out.extend([value & 0xff, value >> 8])

    def append_dba(arg: str, *, line: int, field: str) -> None:
        symbol_info = resolve_symbol(arg)
        if symbol_info is None:
            errors.append(f"line_{line}:unresolved_{field}_label={arg}")
            return
        _, symbol = symbol_info
        bank = int(symbol["bank"]) & 0xff
        address = int(symbol["address"]) & 0xffff
        out.extend([bank, address & 0xff, address >> 8])

    def append_stdscript(arg: str, *, line: int) -> None:
        stdscripts = labels.get("StdScripts")
        target = labels.get(f"{arg.strip()}StdScript")
        if not stdscripts or not target:
            errors.append(f"line_{line}:unresolved_stdscript={arg}")
            return
        delta = int(target["address"]) - int(stdscripts["address"])
        if delta < 0 or delta % 3:
            errors.append(f"line_{line}:invalid_stdscript_index={arg}")
            return
        value = (delta // 3) & 0xffff
        related_symbols.append(f"{arg.strip()}StdScript")
        out.extend([value & 0xff, value >> 8])

    def append_special(arg: str, *, line: int) -> None:
        specials = labels.get("SpecialsPointers")
        target_name = f"{arg.strip()}Special"
        target = labels.get(target_name)
        if not specials or not target:
            errors.append(f"line_{line}:unresolved_special={arg}")
            return
        delta = int(target["address"]) - int(specials["address"])
        if delta < 0 or delta % 3:
            errors.append(f"line_{line}:invalid_special_index={arg}")
            return
        value = (delta // 3) & 0xffff
        related_symbols.append(target_name)
        out.extend([value & 0xff, value >> 8])

    def append_map_id(arg: str, *, line: int) -> None:
        name = arg.strip()
        group = constants.get(f"GROUP_{name}")
        map_number = constants.get(f"MAP_{name}")
        if group is None or map_number is None:
            errors.append(f"line_{line}:unresolved_map_id={name}")
            return
        out.extend([int(group) & 0xff, int(map_number) & 0xff])

    def append_cmdqueue(args: list[str], *, line: int) -> None:
        if len(args) < 2:
            errors.append(f"line_{line}:missing_cmdqueue_args={len(args)}")
            return
        append_u8(args[0], line=line, field="cmdqueue_type")
        append_pointer(args[1], line=line, field="cmdqueue_data")
        append_u16("0", line=line, field="cmdqueue_filler")

    def append_stonetable(args: list[str], *, line: int) -> None:
        if len(args) < 3:
            errors.append(f"line_{line}:missing_stonetable_args={len(args)}")
            return
        append_u8(args[0], line=line, field="stonetable_warp")
        append_u8(args[1], line=line, field="stonetable_object")
        append_pointer(args[2], line=line, field="stonetable_script")

    def append_doorstate(args: list[str], *, line: int) -> None:
        if len(args) < 2:
            errors.append(f"line_{line}:missing_doorstate_args={len(args)}")
            return
        door_id = args[0].strip()
        state = args[1].strip()
        opcode = command_opcode("changeblock", line=line)
        if opcode is not None:
            out.append(opcode)
        append_u8(f"UGDOOR_{door_id}_YCOORD", line=line, field="doorstate_y")
        append_u8(f"UGDOOR_{door_id}_XCOORD", line=line, field="doorstate_x")
        append_u8(f"UNDERGROUND_DOOR_{state}", line=line, field="doorstate_block")

    def append_data_directive(name: str, args: list[str], *, line: int) -> None:
        if name == "db":
            for arg in args:
                append_u8(arg, line=line, field="db")
            return
        if name == "dw":
            for arg in args:
                append_pointer(arg, line=line, field="dw")
            return
        if name == "dn":
            if len(args) % 2:
                errors.append(f"line_{line}:dn_odd_arg_count={len(args)}")
            for pair_index in range(0, len(args) - 1, 2):
                high_text = args[pair_index].strip()
                low_text = args[pair_index + 1].strip()
                high = resolve_numeric(high_text)
                low = resolve_numeric(low_text)
                if high is None or low is None:
                    if high is None:
                        errors.append(f"line_{line}:unresolved_dn_high={high_text}")
                    if low is None:
                        errors.append(f"line_{line}:unresolved_dn_low={low_text}")
                    continue
                out.append(((high & 0x0f) << 4) | (low & 0x0f))
            return
        errors.append(f"line_{line}:unsupported_script_data_directive={name}")

    def append_trainer_record(args: list[str], *, line: int) -> None:
        if len(args) < 7:
            errors.append(f"line_{line}:missing_trainer_args={len(args)}")
            return
        append_u16(args[2], line=line, field="trainer_event_flag")
        append_u8(args[0], line=line, field="trainer_group")
        append_u8(args[1], line=line, field="trainer_id")
        append_pointer(args[3], line=line, field="trainer_seen_text")
        append_pointer(args[4], line=line, field="trainer_win_text")
        append_pointer(args[5], line=line, field="trainer_loss_text")
        append_pointer(args[6], line=line, field="trainer_after_script")

    def append_trainer_name_args(args: list[str], *, line: int) -> None:
        if len(args) < 3:
            errors.append(f"line_{line}:missing_gettrainername_args={len(args)}")
            return
        append_u8(args[1], line=line, field="trainer_name_group")
        append_u8(args[2], line=line, field="trainer_name_id")
        append_u8(args[0], line=line, field="trainer_name_buffer")

    def append_givepoke_args(args: list[str], *, line: int) -> None:
        if len(args) == 2:
            encoded_args = [args[0], args[1], "NO_ITEM", "FALSE"]
        elif len(args) == 3:
            encoded_args = [args[0], args[1], args[2], "FALSE"]
        elif len(args) == 5:
            encoded_args = [args[0], args[1], args[2], "TRUE", args[3], args[4]]
        else:
            encoded_args = args
        if len(encoded_args) < 4:
            errors.append(f"line_{line}:missing_givepoke_args={len(args)}")
            return
        append_u8(encoded_args[0], line=line, field="givepoke_species")
        append_u8(encoded_args[1], line=line, field="givepoke_level")
        append_u8(encoded_args[2], line=line, field="givepoke_item")
        trainer_value = resolve_numeric(encoded_args[3])
        if trainer_value is None:
            errors.append(f"line_{line}:unresolved_givepoke_trainer={encoded_args[3]}")
            return
        out.append(trainer_value & 0xff)
        if trainer_value:
            if len(encoded_args) < 6:
                errors.append(f"line_{line}:missing_givepoke_trainer_names")
                return
            append_pointer(encoded_args[4], line=line, field="givepoke_nickname")
            append_pointer(encoded_args[5], line=line, field="givepoke_ot_name")

    def append_sprite_var(arg: str, *, line: int) -> None:
        value = resolve_numeric(arg)
        sprite_vars = constants.get("SPRITE_VARS")
        if value is None or sprite_vars is None:
            if value is None:
                errors.append(f"line_{line}:unresolved_script_arg_sprite_var={arg}")
            if sprite_vars is None:
                errors.append(f"line_{line}:unresolved_script_constant=SPRITE_VARS")
            return
        out.append((value - int(sprite_vars)) & 0xff)

    for command in dict_items(block.get("commands")):
        name = str(command.get("command", ""))
        line = int(command.get("line", 0))
        args = [str(arg).strip() for arg in command.get("args", [])]
        data_spec = SCRIPT_DATA_MACRO_SPECS.get(name)
        if data_spec is not None:
            if name == "cmdqueue":
                append_cmdqueue(args, line=line)
                continue
            if name == "stonetable":
                append_stonetable(args, line=line)
                continue
            if name == "trainer":
                append_trainer_record(args, line=line)
                continue
            if name == "doorstate":
                append_doorstate(args, line=line)
                continue
            positional_index = 0
            for field_index, kind in enumerate(data_spec, start=1):
                raw_arg = argument(args, positional_index, kind, line=line)
                positional_index += 1
                if raw_arg is None:
                    continue
                if kind == "u8":
                    append_u8(raw_arg, line=line, field=f"script_data_arg_{field_index}")
                elif kind == "u16":
                    append_u16(raw_arg, line=line, field=f"script_data_arg_{field_index}")
                elif kind == "ptr":
                    append_pointer(raw_arg, line=line, field=f"script_data_arg_{field_index}")
                elif kind == "dba":
                    append_dba(raw_arg, line=line, field=f"script_data_arg_{field_index}")
                else:
                    errors.append(f"line_{line}:unsupported_script_data_arg_kind={kind}")
            continue
        spec = SCRIPT_COMMAND_SPECS.get(name)
        if spec is None:
            if name in DATA_BYTE_DIRECTIVES:
                append_data_directive(name, args, line=line)
                continue
            errors.append(f"line_{line}:unsupported_script_command={name}")
            continue
        opcode = command_opcode(name, line=line)
        if opcode is None:
            continue
        out.append(opcode)
        positional_index = 0
        for field_index, kind in enumerate(spec, start=1):
            raw_arg = argument(args, positional_index, kind, line=line)
            if kind not in {"u8_arg_1", "u8_arg_2"}:
                positional_index += 1
            if raw_arg is None:
                continue
            if kind in {"u8", "u8_default_0", "u8_default_1", "u8_arg_1", "u8_arg_2"}:
                append_u8(raw_arg, line=line, field=f"script_arg_{field_index}")
            elif kind == "u8_minus_sprite_vars":
                append_sprite_var(raw_arg, line=line)
            elif kind == "u16":
                append_u16(raw_arg, line=line, field=f"script_arg_{field_index}")
            elif kind == "money24":
                append_money24(raw_arg, line=line, field=f"script_arg_{field_index}")
            elif kind == "ptr":
                append_pointer(raw_arg, line=line, field=f"script_arg_{field_index}")
            elif kind == "ptr_arg_2":
                append_pointer(raw_arg, line=line, field=f"script_arg_{field_index}")
            elif kind == "dba":
                append_dba(raw_arg, line=line, field=f"script_arg_{field_index}")
            elif kind == "stdscript":
                append_stdscript(raw_arg, line=line)
            elif kind == "special":
                append_special(raw_arg, line=line)
            elif kind == "map_id":
                append_map_id(raw_arg, line=line)
            elif kind == "trainername":
                append_trainer_name_args(args, line=line)
            elif kind == "givepoke":
                append_givepoke_args(args, line=line)
            else:
                errors.append(f"line_{line}:unsupported_script_arg_kind={kind}")

    if not out and block.get("commands"):
        errors.append("no_script_command_bytes_encoded")
    return {
        "bytes": out,
        "errors": unique_list(errors),
        "related_symbols": unique_list(related_symbols),
    }


def script_symbol_name(label: str, *, block_label: str) -> str:
    if label.startswith(".") and block_label:
        return f"{block_label}{label}"
    return label


def text_block_rom_mirror_invariants(
    parsed: dict[str, Any],
    *,
    source_file: str,
    rom_context: dict[str, Any],
) -> list[dict[str, Any]]:
    if not rom_context.get("available"):
        return []
    out: list[dict[str, Any]] = []
    for block in parsed.get("text_blocks", []):
        label = str(block.get("label", ""))
        if not label:
            continue
        commands = [
            f"python -m tools.debugger content-mirror --source-file {source_file}",
            f"python -m tools.debugger provenance --symbol {label}",
            f"python -m tools.debugger compare --changed-file {source_file}",
        ]
        related_files = [
            source_file,
            str(rom_context.get("rom_path", "")),
            str(rom_context.get("symbols_path", "")),
        ]
        symbol = rom_context.get("labels", {}).get(label)
        if not symbol:
            out.append(
                content_invariant(
                    invariant_id=f"{source_file}:text_block_rom_bytes:{label}",
                    invariant_type="text_block_rom_bytes",
                    status="warning",
                    severity=50,
                    title=f"{label} text block is missing from built ROM symbols",
                    source_file=source_file,
                    line=int(block.get("line", 0)),
                    evidence=[
                        f"label={label}",
                        f"symbols={rom_context.get('symbols_path', '')}",
                    ],
                    commands=commands,
                    related_files=related_files,
                    related_symbols=[label],
                )
            )
            continue
        encoded = encode_text_block(
            block,
            rom_context=rom_context,
            source_constants=parsed.get("constants", {}),
        )
        if encoded["errors"]:
            out.append(
                content_invariant(
                    invariant_id=f"{source_file}:text_block_rom_bytes:{label}",
                    invariant_type="text_block_rom_bytes",
                    status="warning",
                    severity=56,
                    title=f"{label} text block could not be fully encoded for ROM byte comparison",
                    source_file=source_file,
                    line=int(block.get("line", 0)),
                    evidence=[
                        f"label={label}",
                        f"command_count={len(block.get('commands', []))}",
                        *encoded["errors"][:12],
                    ],
                    commands=commands,
                    related_files=related_files,
                    related_symbols=[label],
                )
            )
            continue
        expected = bytes(encoded["bytes"])
        if not expected:
            continue
        rom_bytes = rom_context.get("rom_bytes", b"")
        offset = int(symbol["rom_offset"])
        actual = rom_bytes[offset:offset + len(expected)]
        short_read = len(actual) != len(expected)
        mismatch_index = first_mismatch(expected, actual) if not short_read else min(len(actual), max(0, len(expected) - 1))
        matched = not short_read and mismatch_index < 0
        evidence = [
            f"label={label}",
            f"command_count={len(block.get('commands', []))}",
            f"bank=${int(symbol['bank']):02x}",
            f"address=${int(symbol['address']):04x}",
            f"rom_offset=${offset:06x}",
            f"expected_len={len(expected)}",
            f"actual_len={len(actual)}",
            f"expected_sha256={hashlib.sha256(expected).hexdigest()}",
            f"actual_sha256={hashlib.sha256(actual).hexdigest()}",
        ]
        if mismatch_index >= 0:
            expected_byte = expected[mismatch_index] if mismatch_index < len(expected) else None
            actual_byte = actual[mismatch_index] if mismatch_index < len(actual) else None
            evidence.append(
                "first_mismatch="
                f"{mismatch_index} expected={format_optional_byte(expected_byte)} actual={format_optional_byte(actual_byte)}"
            )
            evidence.append(f"expected_window={hex_window(expected, mismatch_index)}")
            evidence.append(f"actual_window={hex_window(actual, mismatch_index)}")
        out.append(
            content_invariant(
                invariant_id=f"{source_file}:text_block_rom_bytes:{label}",
                invariant_type="text_block_rom_bytes",
                status="passed" if matched else "failed",
                severity=0 if matched else 88,
                title=(
                    f"{label} ROM bytes match source text block"
                    if matched
                    else f"{label} ROM bytes differ from source text block"
                ),
                source_file=source_file,
                line=int(block.get("line", 0)),
                evidence=evidence,
                commands=commands,
                related_files=related_files,
                related_symbols=[label],
            )
        )
    return out


def encode_text_block(
    block: dict[str, Any],
    *,
    rom_context: dict[str, Any],
    source_constants: dict[str, int] | None = None,
) -> dict[str, Any]:
    out: list[int] = []
    errors: list[str] = []
    constants = {**rom_context.get("constants", {}), **(source_constants or {})}
    labels = rom_context.get("labels", {})
    charmap = rom_context.get("charmap", {})
    if not isinstance(charmap, dict) or not charmap:
        errors.append("missing_charmap")
        return {"bytes": out, "errors": errors}

    def resolve_text_pointer(arg: str) -> int | None:
        value = evaluate_int_expression(arg, constants)
        if value is not None:
            return value
        symbol = labels.get(arg.strip())
        if not symbol:
            return None
        return int(symbol["address"])

    for command in dict_items(block.get("commands")):
        name = str(command.get("command", ""))
        line = int(command.get("line", 0))
        args = [str(arg).strip() for arg in command.get("args", [])]
        if name in TEXT_LINE_MACROS:
            prefix = TEXT_LINE_MACROS[name]
            if prefix.startswith("TX_"):
                value = constants.get(prefix)
                if value is None:
                    errors.append(f"line_{line}:unresolved_text_constant={prefix}")
                else:
                    out.append(int(value) & 0xff)
            else:
                append_charmap_token(out, prefix, charmap=charmap, errors=errors, line=line)
            if len(args) != 1 or not is_quoted_rgbds_string(args[0]):
                errors.append(f"line_{line}:unsupported_text_args={','.join(args)}")
                continue
            expanded = expand_rgbds_string_formats(args[0][1:-1], constants=constants, errors=errors, line=line)
            out.extend(encode_charmap_string(expanded, charmap=charmap, errors=errors, line=line))
            continue
        if name in TEXT_TERMINATOR_MACROS:
            append_charmap_token(out, TEXT_TERMINATOR_MACROS[name], charmap=charmap, errors=errors, line=line)
            continue
        spec = TEXT_COMMAND_SPECS.get(name)
        if spec is None:
            errors.append(f"line_{line}:unsupported_text_command={name}")
            continue
        positional_index = 0
        for field in spec:
            if field.startswith("const:"):
                constant_name = field.split(":", 1)[1]
                value = constants.get(constant_name)
                if value is None:
                    errors.append(f"line_{line}:unresolved_text_constant={constant_name}")
                else:
                    out.append(int(value) & 0xff)
                continue
            if field == "u8":
                if positional_index >= len(args):
                    errors.append(f"line_{line}:missing_text_arg_{positional_index + 1}")
                    continue
                value = evaluate_int_expression(args[positional_index], constants)
                if value is None:
                    errors.append(f"line_{line}:unresolved_text_arg_{positional_index + 1}={args[positional_index]}")
                    positional_index += 1
                    continue
                out.append(value & 0xff)
                positional_index += 1
                continue
            if field == "ptr":
                if positional_index >= len(args):
                    errors.append(f"line_{line}:missing_text_arg_{positional_index + 1}")
                    continue
                value = resolve_text_pointer(args[positional_index])
                if value is None:
                    errors.append(f"line_{line}:unresolved_text_pointer_{positional_index + 1}={args[positional_index]}")
                    positional_index += 1
                    continue
                value &= 0xffff
                out.extend([value & 0xff, value >> 8])
                positional_index += 1
                continue
            errors.append(f"line_{line}:unsupported_text_field={field}")
    if not out and block.get("commands"):
        errors.append("no_text_block_bytes_encoded")
    return {"bytes": out, "errors": unique_list(errors)}


def movement_data_rom_mirror_invariants(
    parsed: dict[str, Any],
    *,
    source_file: str,
    rom_context: dict[str, Any],
) -> list[dict[str, Any]]:
    if not rom_context.get("available"):
        return []
    out: list[dict[str, Any]] = []
    for block in parsed.get("movement_blocks", []):
        label = str(block.get("label", ""))
        if not label:
            continue
        commands = [
            f"python -m tools.debugger content-mirror --source-file {source_file}",
            f"python -m tools.debugger provenance --symbol {label}",
            f"python -m tools.debugger replay --changed-file {source_file} --scenario-id {label}",
            f"python -m tools.debugger compare --changed-file {source_file}",
        ]
        related_files = [
            source_file,
            str(rom_context.get("rom_path", "")),
            str(rom_context.get("symbols_path", "")),
        ]
        symbol = rom_context.get("labels", {}).get(label)
        if not symbol:
            out.append(
                content_invariant(
                    invariant_id=f"{source_file}:movement_data_rom_bytes:{label}",
                    invariant_type="movement_data_rom_bytes",
                    status="warning",
                    severity=50,
                    title=f"{label} movement data is missing from built ROM symbols",
                    source_file=source_file,
                    line=int(block.get("line", 0)),
                    evidence=[
                        f"label={label}",
                        f"symbols={rom_context.get('symbols_path', '')}",
                    ],
                    commands=commands,
                    related_files=related_files,
                    related_symbols=[label],
                )
            )
            continue
        encoded = encode_movement_block(
            block,
            rom_context=rom_context,
            source_constants=parsed.get("constants", {}),
        )
        if encoded["errors"]:
            out.append(
                content_invariant(
                    invariant_id=f"{source_file}:movement_data_rom_bytes:{label}",
                    invariant_type="movement_data_rom_bytes",
                    status="warning",
                    severity=56,
                    title=f"{label} movement data could not be fully encoded for ROM byte comparison",
                    source_file=source_file,
                    line=int(block.get("line", 0)),
                    evidence=[
                        f"label={label}",
                        f"command_count={len(block.get('commands', []))}",
                        *encoded["errors"][:12],
                    ],
                    commands=commands,
                    related_files=related_files,
                    related_symbols=[label],
                )
            )
            continue
        expected = bytes(encoded["bytes"])
        if not expected:
            continue
        rom_bytes = rom_context.get("rom_bytes", b"")
        offset = int(symbol["rom_offset"])
        actual = rom_bytes[offset:offset + len(expected)]
        short_read = len(actual) != len(expected)
        mismatch_index = first_mismatch(expected, actual) if not short_read else min(len(actual), max(0, len(expected) - 1))
        matched = not short_read and mismatch_index < 0
        evidence = [
            f"label={label}",
            f"command_count={len(block.get('commands', []))}",
            f"bank=${int(symbol['bank']):02x}",
            f"address=${int(symbol['address']):04x}",
            f"rom_offset=${offset:06x}",
            f"expected_len={len(expected)}",
            f"actual_len={len(actual)}",
            f"expected_sha256={hashlib.sha256(expected).hexdigest()}",
            f"actual_sha256={hashlib.sha256(actual).hexdigest()}",
        ]
        if mismatch_index >= 0:
            expected_byte = expected[mismatch_index] if mismatch_index < len(expected) else None
            actual_byte = actual[mismatch_index] if mismatch_index < len(actual) else None
            evidence.append(
                "first_mismatch="
                f"{mismatch_index} expected={format_optional_byte(expected_byte)} actual={format_optional_byte(actual_byte)}"
            )
            evidence.append(f"expected_window={hex_window(expected, mismatch_index)}")
            evidence.append(f"actual_window={hex_window(actual, mismatch_index)}")
        out.append(
            content_invariant(
                invariant_id=f"{source_file}:movement_data_rom_bytes:{label}",
                invariant_type="movement_data_rom_bytes",
                status="passed" if matched else "failed",
                severity=0 if matched else 90,
                title=(
                    f"{label} ROM bytes match source movement data"
                    if matched
                    else f"{label} ROM bytes differ from source movement data"
                ),
                source_file=source_file,
                line=int(block.get("line", 0)),
                evidence=evidence,
                commands=commands,
                related_files=related_files,
                related_symbols=[label],
            )
        )
    return out


def encode_movement_block(
    block: dict[str, Any],
    *,
    rom_context: dict[str, Any],
    source_constants: dict[str, int] | None = None,
) -> dict[str, Any]:
    out: list[int] = []
    errors: list[str] = []
    constants = {**rom_context.get("constants", {}), **(source_constants or {})}

    def constant_value(name: str, *, line: int) -> int | None:
        value = constants.get(name)
        if value is None:
            errors.append(f"line_{line}:unresolved_movement_constant={name}")
            return None
        return int(value)

    def argument(args: list[str], index: int, *, field: str, line: int) -> str | None:
        if index >= len(args):
            errors.append(f"line_{line}:missing_{field}")
            return None
        return args[index]

    def numeric_value(raw: str, *, field: str, line: int) -> int | None:
        value = evaluate_int_expression(raw, constants)
        if value is None:
            errors.append(f"line_{line}:unresolved_{field}={raw}")
            return None
        return value

    for command in dict_items(block.get("commands")):
        name = str(command.get("command", ""))
        line = int(command.get("line", 0))
        args = [str(arg).strip() for arg in command.get("args", [])]
        if name in MOVEMENT_DIRECTIONAL_MACROS:
            base = constant_value(MOVEMENT_DIRECTIONAL_MACROS[name], line=line)
            raw_direction = argument(args, 0, field="movement_direction", line=line)
            if base is None or raw_direction is None:
                continue
            direction = numeric_value(raw_direction, field="movement_direction", line=line)
            if direction is not None:
                out.append((base | direction) & 0xff)
            continue
        if name in MOVEMENT_NO_ARG_MACROS:
            value = constant_value(MOVEMENT_NO_ARG_MACROS[name], line=line)
            if value is not None:
                out.append(value & 0xff)
            continue
        if name in MOVEMENT_U8_ARG_MACROS:
            opcode = constant_value(MOVEMENT_U8_ARG_MACROS[name], line=line)
            raw_value = argument(args, 0, field="movement_arg_1", line=line)
            if opcode is None or raw_value is None:
                continue
            value = numeric_value(raw_value, field="movement_arg_1", line=line)
            if value is not None:
                out.extend([opcode & 0xff, value & 0xff])
            continue
        if name == "step_sleep":
            base = constant_value("movement_step_sleep", line=line)
            raw_value = argument(args, 0, field="movement_arg_1", line=line)
            if base is None or raw_value is None:
                continue
            value = numeric_value(raw_value, field="movement_arg_1", line=line)
            if value is None:
                continue
            if value <= 8:
                out.append((base + value - 1) & 0xff)
            else:
                out.extend([(base + 8) & 0xff, value & 0xff])
            continue
        errors.append(f"line_{line}:unsupported_movement_command={name}")

    if not out and block.get("commands"):
        errors.append("no_movement_bytes_encoded")
    return {"bytes": out, "errors": unique_list(errors)}


def append_charmap_token(
    out: list[int],
    token: str,
    *,
    charmap: dict[str, int],
    errors: list[str],
    line: int,
) -> None:
    value = charmap.get(token)
    if value is None:
        errors.append(f"line_{line}:unresolved_charmap_token={token}")
        return
    out.append(int(value) & 0xff)


def expand_rgbds_string_formats(
    text: str,
    *,
    constants: dict[str, int],
    errors: list[str],
    line: int,
) -> str:
    def replace_decimal(match: re.Match[str]) -> str:
        expr = match.group("expr").strip()
        value = evaluate_int_expression(expr, constants)
        if value is None:
            errors.append(f"line_{line}:unresolved_text_decimal={expr}")
            return ""
        return str(value)

    return RGBDS_DECIMAL_FORMAT_RE.sub(replace_decimal, text)


def encode_charmap_string(
    text: str,
    *,
    charmap: dict[str, int],
    errors: list[str],
    line: int,
) -> list[int]:
    out: list[int] = []
    tokens = sorted((str(token) for token in charmap), key=len, reverse=True)
    index = 0
    while index < len(text):
        match = next((token for token in tokens if text.startswith(token, index)), "")
        if not match:
            errors.append(f"line_{line}:unmapped_text={text[index]}")
            index += 1
            continue
        out.append(int(charmap[match]) & 0xff)
        index += len(match)
    return out


def object_constant_invariants(parsed: dict[str, Any], *, source_file: str) -> list[dict[str, Any]]:
    if not is_map_event_file(source_file, parsed):
        return []
    object_const_count = int(parsed.get("object_const_count", 0))
    object_event_count = len(parsed["macro_lines"].get("object_event", []))
    if not object_const_count or not object_event_count:
        return []
    matches = object_const_count == object_event_count
    return [
        content_invariant(
            invariant_id=f"{source_file}:object_constants_match_events",
            invariant_type="object_constants_match_events",
            status="passed" if matches else "warning",
            severity=45 if not matches else 0,
            title=(
                f"object constants match object events in {source_file}"
                if matches
                else f"object constants differ from object events in {source_file}"
            ),
            source_file=source_file,
            evidence=[
                f"object_const_count={object_const_count}",
                f"object_event_count={object_event_count}",
            ],
            commands=source_commands(source_file),
            related_files=[source_file],
        )
    ]


def map_event_rom_mirror_invariants(
    parsed: dict[str, Any],
    text: str,
    *,
    source_file: str,
    rom_context: dict[str, Any],
) -> list[dict[str, Any]]:
    if not rom_context.get("available") or not is_map_event_file(source_file, parsed):
        return []
    table = parse_map_event_table(text)
    if not table:
        return []

    label = str(table["label"])
    symbol = rom_context.get("labels", {}).get(label)
    commands = [
        f"python -m tools.debugger content-mirror --source-file {source_file}",
        f"python -m tools.debugger provenance --source-file {source_file}",
        f"python -m tools.debugger compare --changed-file {source_file}",
    ]
    if not symbol:
        return [
            content_invariant(
                invariant_id=f"{source_file}:map_event_rom_bytes",
                invariant_type="map_event_rom_bytes",
                status="failed",
                severity=86,
                title=f"{label} is missing from the built ROM symbols",
                source_file=source_file,
                line=int(table.get("line", 0)),
                evidence=[
                    f"label={label}",
                    f"symbols={rom_context.get('symbols_path', '')}",
                ],
                commands=commands,
                related_files=[source_file, str(rom_context.get("rom_path", "")), str(rom_context.get("symbols_path", ""))],
                related_symbols=[label],
            )
        ]

    encoded = encode_map_event_table(table, rom_context=rom_context)
    if encoded["errors"]:
        return [
            content_invariant(
                invariant_id=f"{source_file}:map_event_rom_bytes",
                invariant_type="map_event_rom_bytes",
                status="warning",
                severity=55,
                title=f"{label} could not be fully encoded for ROM byte comparison",
                source_file=source_file,
                line=int(table.get("line", 0)),
                evidence=[
                    f"label={label}",
                    *encoded["errors"][:10],
                ],
                commands=commands,
                related_files=[source_file, str(rom_context.get("rom_path", "")), str(rom_context.get("symbols_path", ""))],
                related_symbols=[label, *encoded["related_symbols"]],
            )
        ]

    expected = bytes(encoded["bytes"])
    rom_bytes = rom_context.get("rom_bytes", b"")
    offset = int(symbol["rom_offset"])
    actual = rom_bytes[offset:offset + len(expected)]
    short_read = len(actual) != len(expected)
    mismatch_index = first_mismatch(expected, actual) if not short_read else min(len(actual), len(expected) - 1)
    matched = not short_read and mismatch_index < 0
    evidence = [
        f"label={label}",
        f"bank=${int(symbol['bank']):02x}",
        f"address=${int(symbol['address']):04x}",
        f"rom_offset=${offset:06x}",
        f"expected_len={len(expected)}",
        f"actual_len={len(actual)}",
        f"expected_sha256={hashlib.sha256(expected).hexdigest()}",
        f"actual_sha256={hashlib.sha256(actual).hexdigest()}",
    ]
    if mismatch_index >= 0:
        expected_byte = expected[mismatch_index] if mismatch_index < len(expected) else None
        actual_byte = actual[mismatch_index] if mismatch_index < len(actual) else None
        evidence.append(
            "first_mismatch="
            f"{mismatch_index} expected={format_optional_byte(expected_byte)} actual={format_optional_byte(actual_byte)}"
        )
        evidence.append(f"expected_window={hex_window(expected, mismatch_index)}")
        evidence.append(f"actual_window={hex_window(actual, mismatch_index)}")

    return [
        content_invariant(
            invariant_id=f"{source_file}:map_event_rom_bytes",
            invariant_type="map_event_rom_bytes",
            status="passed" if matched else "failed",
            severity=0 if matched else 90,
            title=(
                f"{label} ROM bytes match source map events"
                if matched
                else f"{label} ROM bytes differ from source map events"
            ),
            source_file=source_file,
            line=int(table.get("line", 0)),
            evidence=evidence,
            commands=commands,
            related_files=[source_file, str(rom_context.get("rom_path", "")), str(rom_context.get("symbols_path", ""))],
            related_symbols=[label, *encoded["related_symbols"]],
        )
    ]


def parse_map_event_table(text: str) -> dict[str, Any] | None:
    lines = text.splitlines()
    table: dict[str, Any] | None = None
    current_section = ""
    section_by_macro = {section_macro: event_macro for event_macro, section_macro in MAP_SECTION_MACROS.items()}
    for index, raw_line in enumerate(lines, start=1):
        clean = strip_comment(raw_line).strip()
        if not clean:
            continue
        label, code = split_label(clean)
        if label and not label.startswith("."):
            if table is None and label.endswith("_MapEvents"):
                table = {
                    "label": label,
                    "line": index,
                    "filler": [],
                    "warp_event": [],
                    "coord_event": [],
                    "bg_event": [],
                    "object_event": [],
                }
                current_section = ""
            elif table is not None:
                break
        if table is None:
            continue
        token = first_token(code)
        if not token:
            continue
        if token == "db" and not current_section:
            table["filler"].extend(split_macro_args(code[len(token):]))
            continue
        if token in section_by_macro:
            current_section = section_by_macro[token]
            continue
        if token in MAP_SECTION_MACROS:
            table[token].append(
                {
                    "line": index,
                    "fields": split_macro_args(code[len(token):]),
                }
            )
    return table


def encode_map_event_table(table: dict[str, Any], *, rom_context: dict[str, Any]) -> dict[str, Any]:
    out: list[int] = []
    errors: list[str] = []
    related_symbols: list[str] = []
    constants = rom_context.get("constants", {})
    labels = rom_context.get("labels", {})

    def add_error(message: str) -> None:
        errors.append(message)

    def resolve(expr: str, *, field: str) -> int | None:
        value = evaluate_int_expression(expr, constants)
        if value is None:
            add_error(f"unresolved_{field}={expr}")
            return None
        return value

    def append_u8(expr: str, *, field: str, add: int = 0) -> None:
        value = resolve(expr, field=field)
        if value is None:
            return
        out.append((value + add) & 0xff)

    def append_u16(expr: str, *, field: str) -> None:
        value = resolve(expr, field=field)
        if value is None:
            return
        value &= 0xffff
        out.extend([value & 0xff, value >> 8])

    def append_pointer(label_expr: str, *, field: str) -> None:
        label = label_expr.strip()
        symbol = labels.get(label)
        if not symbol:
            add_error(f"unresolved_{field}_label={label}")
            return
        related_symbols.append(label)
        address = int(symbol["address"]) & 0xffff
        out.extend([address & 0xff, address >> 8])

    def append_dn(high_expr: str, low_expr: str, *, field: str) -> None:
        high = resolve(high_expr, field=f"{field}_high")
        low = resolve(low_expr, field=f"{field}_low")
        if high is None or low is None:
            return
        out.append(((high & 0x0f) << 4) | (low & 0x0f))

    for filler in table.get("filler", []):
        append_u8(str(filler), field="filler")

    warps = list(table.get("warp_event", []))
    append_count(out, warps, "warp_event", errors)
    for row in warps:
        fields = padded_fields(row, 4)
        append_u8(fields[1], field="warp_y")
        append_u8(fields[0], field="warp_x")
        append_u8(fields[3], field="warp_destination")
        map_name = fields[2].strip()
        append_u8(f"GROUP_{map_name}", field="warp_group")
        append_u8(f"MAP_{map_name}", field="warp_map")

    coords = list(table.get("coord_event", []))
    append_count(out, coords, "coord_event", errors)
    for row in coords:
        fields = padded_fields(row, 4)
        append_u8(fields[2], field="coord_scene")
        append_u8(fields[1], field="coord_y")
        append_u8(fields[0], field="coord_x")
        out.append(0)
        append_pointer(fields[3], field="coord_script")
        out.extend([0, 0])

    bg_events = list(table.get("bg_event", []))
    append_count(out, bg_events, "bg_event", errors)
    for row in bg_events:
        fields = padded_fields(row, 4)
        append_u8(fields[1], field="bg_y")
        append_u8(fields[0], field="bg_x")
        append_u8(fields[2], field="bg_type")
        append_pointer(fields[3], field="bg_script")

    objects = list(table.get("object_event", []))
    append_count(out, objects, "object_event", errors)
    for row in objects:
        fields = padded_fields(row, 13)
        append_u8(fields[2], field="object_sprite")
        append_u8(fields[1], field="object_y", add=4)
        append_u8(fields[0], field="object_x", add=4)
        append_u8(fields[3], field="object_movement")
        append_dn(fields[5], fields[4], field="object_radius")
        append_u8(fields[6], field="object_hour1")
        append_u8(fields[7], field="object_hour2")
        append_dn(fields[8], fields[9], field="object_palette_type")
        append_u8(fields[10], field="object_sight")
        append_pointer(fields[11], field="object_script")
        append_u16(fields[12], field="object_event_flag")

    return {
        "bytes": out,
        "errors": unique_list(errors),
        "related_symbols": unique_list(related_symbols),
    }


def padded_fields(row: dict[str, Any], count: int) -> list[str]:
    fields = [str(item).strip() for item in row.get("fields", [])]
    if len(fields) < count:
        fields.extend([""] * (count - len(fields)))
    return fields


def append_count(out: list[int], rows: list[dict[str, Any]], section: str, errors: list[str]) -> None:
    count = len(rows)
    if count > 0xff:
        errors.append(f"{section}_count_too_large={count}")
    out.append(count & 0xff)


def load_rom_mirror_context(*, rom_path: str, symbols_path: str, root: Path) -> dict[str, Any]:
    rom = resolve_path(rom_path, root=root) if rom_path else root / DEFAULT_ROM_PATH
    symbols = resolve_path(symbols_path, root=root) if symbols_path else root / DEFAULT_SYMBOLS_PATH
    context: dict[str, Any] = {
        "available": False,
        "rom_path": display_path(rom, root=root),
        "symbols_path": display_path(symbols, root=root),
        "rom_bytes": b"",
        "labels": {},
        "constants": {},
        "charmap": {},
    }
    if not rom.exists() or not rom.is_file() or not symbols.exists() or not symbols.is_file():
        return context
    try:
        symbol_table = load_symbol_table(symbols)
        constants = load_map_event_constants(root=root, symbol_constants=symbol_table["constants"])
        context.update(
            {
                "available": True,
                "rom_bytes": rom.read_bytes(),
                "labels": symbol_table["labels"],
                "constants": constants,
                "charmap": load_charmap(root=root, constants=constants),
            }
        )
    except OSError:
        return context
    return context


def load_symbol_table(path: Path) -> dict[str, Any]:
    labels: dict[str, dict[str, int]] = {}
    constants: dict[str, int] = {}
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith(";"):
            continue
        label_match = SYM_LABEL_RE.match(line)
        if label_match:
            bank = int(label_match.group("bank"), 16)
            address = int(label_match.group("addr"), 16)
            labels[label_match.group("label")] = {
                "bank": bank,
                "address": address,
                "rom_offset": rom_offset_for_symbol(bank=bank, address=address),
            }
            continue
        constant_match = SYM_CONSTANT_RE.match(line)
        if constant_match:
            constants[constant_match.group("label")] = int(constant_match.group("value"), 16)
    return {"labels": labels, "constants": constants}


def rom_offset_for_symbol(*, bank: int, address: int) -> int:
    if address < 0x4000:
        return address
    return bank * 0x4000 + (address - 0x4000)


def load_map_event_constants(*, root: Path, symbol_constants: dict[str, int]) -> dict[str, int]:
    constants: dict[str, int] = base_rgbds_constants()
    constants_dir = root / "constants"
    if constants_dir.exists() and constants_dir.is_dir():
        for path in sorted(constants_dir.glob("*.asm")):
            parse_constant_file(path, constants)
    parse_constant_file(root / "macros" / "scripts" / "events.asm", constants)
    parse_constant_file(root / "macros" / "scripts" / "text.asm", constants)
    parse_constant_file(root / "macros" / "scripts" / "movement.asm", constants)
    parse_map_constants(root / "constants" / "map_constants.asm", constants)
    for name, value in symbol_constants.items():
        constants.setdefault(name, value)
    return constants


def base_rgbds_constants() -> dict[str, int]:
    return {
        "TILE_SIZE": 16,
        "TILE_1BPP_SIZE": 8,
        "TILE_2BPP_SIZE": 16,
        "COLOR_SIZE": 2,
        "PAL_SIZE": 8,
    }


def load_charmap(*, root: Path, constants: dict[str, int]) -> dict[str, int]:
    charmap: dict[str, int] = {}
    for path in [root / "constants" / "charmap.asm", root / "macros" / "legacy.asm"]:
        if not path.exists():
            continue
        for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            clean = strip_comment(raw_line).strip()
            match = CHARMAP_RE.match(clean)
            if not match:
                continue
            token = unescape_rgbds_string(match.group("token"))
            value = parse_charmap_value(match.group("value"), charmap=charmap, constants=constants)
            if value is not None:
                charmap[token] = value & 0xff
    return charmap


def parse_charmap_value(value: str, *, charmap: dict[str, int], constants: dict[str, int]) -> int | None:
    text = value.strip().rstrip(",")
    if len(text) >= 2 and text[0] == "'" and text[-1] == "'":
        return charmap.get(text[1:-1])
    return evaluate_int_expression(text, constants)


def unescape_rgbds_string(text: str) -> str:
    return text.replace(r"\"", '"').replace(r"\\", "\\")


def parse_map_constants(path: Path, constants: dict[str, int]) -> None:
    if not path.exists():
        return
    const_value = 0
    const_inc = 1
    current_group = 0
    map_value = 1
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        clean = strip_comment(raw_line).strip()
        if not clean:
            continue
        token = first_token(clean)
        args = split_macro_args(clean[len(token):])
        if token == "const_def":
            const_value = evaluate_int_expression(args[0], constants) if args else 0
            const_inc = evaluate_int_expression(args[1], constants) if len(args) > 1 else 1
            const_value = 0 if const_value is None else const_value
            const_inc = 1 if const_inc is None else const_inc
            continue
        if token == "newgroup":
            const_value += const_inc
            current_group = const_value
            map_value = 1
            if args:
                constants[f"MAPGROUP_{args[0]}"] = current_group
            continue
        if token == "map_const" and args:
            name = args[0]
            constants[f"GROUP_{name}"] = current_group
            constants[f"MAP_{name}"] = map_value
            map_value += 1


def parse_constant_file(path: Path, constants: dict[str, int]) -> None:
    if not path.exists():
        return
    const_value = 0
    const_inc = 1
    in_macro_definition = False

    def resolve(expr: str) -> int | None:
        local_constants = {**constants, "const_value": const_value, "const_inc": const_inc}
        return evaluate_int_expression(expr, local_constants)

    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        clean = strip_comment(raw_line).strip()
        if not clean:
            continue
        token = first_token(clean)
        args = split_macro_args(clean[len(token):])
        if token == "MACRO":
            in_macro_definition = True
            continue
        if token == "ENDM":
            in_macro_definition = False
            continue
        if in_macro_definition:
            continue
        if token == "const_def":
            value = resolve(args[0]) if args else 0
            inc = resolve(args[1]) if len(args) > 1 else 1
            const_value = 0 if value is None else value
            const_inc = 1 if inc is None else inc
            continue
        if token == "trainerclass" and args:
            trainer_class = int(constants.get("__trainer_class__", 0))
            constants[args[0]] = trainer_class
            constants["__trainer_class__"] = trainer_class + 1
            const_value = 1
            const_inc = 1
            continue
        if token in {"add_tm", "add_hm"} and args:
            move_name = args[0]
            prefix = "TM" if token == "add_tm" else "HM"
            tmhm_value = int(constants.get("__tmhm_value__", 1))
            constants[f"{prefix}_{move_name}"] = const_value
            constants[f"{move_name}_TMNUM"] = tmhm_value
            move_value = constants.get(move_name)
            if move_value is not None:
                constants[f"{prefix}{tmhm_value:02d}_MOVE"] = move_value
            constants["__tmhm_value__"] = tmhm_value + 1
            const_value += const_inc
            continue
        if token == "const" and args:
            constants[args[0]] = const_value
            const_value += const_inc
            continue
        if token == "shift_const" and args:
            if const_value >= 0:
                constants[args[0]] = 1 << const_value
            constants[f"{args[0]}_F"] = const_value
            const_value += const_inc
            continue
        if token == "const_skip":
            count = resolve(args[0]) if args else 1
            const_value += const_inc * (1 if count is None else count)
            continue
        if token == "const_next" and args:
            value = resolve(args[0])
            if value is not None:
                const_value = value
            continue
        assign_match = DEF_ASSIGN_RE.match(clean)
        if assign_match:
            value = resolve(assign_match.group("expr"))
            if value is not None:
                name = assign_match.group("name")
                if name == "const_inc":
                    const_inc = value
                elif name == "const_value":
                    const_value = value
                else:
                    constants[name] = value
            continue
        equ_match = DEF_EQU_RE.match(clean)
        if equ_match:
            value = resolve(equ_match.group("expr"))
            if value is not None:
                constants[equ_match.group("name")] = value
            continue
        equs_match = DEF_EQUS_RE.match(clean)
        if equs_match and equs_match.group("value") in constants:
            constants[equs_match.group("name")] = constants[equs_match.group("value")]


def evaluate_int_expression(expr: str, constants: dict[str, int]) -> int | None:
    text = str(expr).strip()
    if not text:
        return None
    if text in constants:
        return int(constants[text])
    text = re.sub(r"\$([0-9A-Fa-f]+)", r"0x\1", text)
    text = re.sub(r"%([01]+)", r"0b\1", text)
    unresolved: list[str] = []

    def replace_name(match: re.Match[str]) -> str:
        name = match.group(0)
        if name in constants:
            return str(constants[name])
        unresolved.append(name)
        return name

    text = re.sub(r"\b[A-Za-z_.$][A-Za-z0-9_.$]*\b", replace_name, text)
    if unresolved:
        return None
    if not re.fullmatch(r"[0-9xXa-fA-FbBoO\s<>()+\-*/|&]+", text):
        return None
    try:
        return int(eval(text, {"__builtins__": {}}, {}))
    except (ArithmeticError, NameError, SyntaxError, TypeError, ValueError):
        return None


def split_macro_args(text: str) -> list[str]:
    fields = []
    current = []
    in_quote = False
    depth = 0
    for char in text.strip():
        if char == '"':
            in_quote = not in_quote
        elif not in_quote and char in "([{":
            depth += 1
        elif not in_quote and char in ")]}" and depth:
            depth -= 1
        if char == "," and not in_quote and depth == 0:
            fields.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    if current:
        fields.append("".join(current).strip())
    return fields


def first_mismatch(expected: bytes, actual: bytes) -> int:
    for index, (expected_byte, actual_byte) in enumerate(zip(expected, actual)):
        if expected_byte != actual_byte:
            return index
    if len(expected) != len(actual):
        return min(len(expected), len(actual))
    return -1


def format_optional_byte(value: int | None) -> str:
    return "<missing>" if value is None else f"${value:02x}"


def hex_window(data: bytes, index: int, *, radius: int = 8) -> str:
    if not data:
        return "<empty>"
    start = max(0, index - radius)
    end = min(len(data), index + radius + 1)
    return " ".join(f"{byte:02x}" for byte in data[start:end])


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


def parse_script_blocks(lines: list[str]) -> list[dict[str, Any]]:
    script_tokens = set(SCRIPT_COMMAND_SPECS) | set(SCRIPT_DATA_MACRO_SPECS)
    non_script_tokens = (
        NON_SCRIPT_BLOCK_START_TOKENS
        | set(MOVEMENT_DIRECTIONAL_MACROS)
        | set(MOVEMENT_NO_ARG_MACROS)
        | set(MOVEMENT_U8_ARG_MACROS)
        | MOVEMENT_SPECIAL_MACROS
    )
    blocks: list[dict[str, Any]] = []
    current_global_label = ""
    current_block: dict[str, Any] | None = None

    def finish_block() -> None:
        nonlocal current_block
        if current_block and current_block.get("commands"):
            blocks.append(current_block)
        current_block = None

    for index, raw_line in enumerate(lines, start=1):
        clean = strip_comment(raw_line).strip()
        if not clean:
            continue
        label, code = split_label(clean)
        if label and label.startswith(".") and current_block is not None:
            commands = current_block.get("commands", [])
            previous_command = str(commands[-1].get("command", "")) if commands else ""
            if previous_command in SCRIPT_TERMINAL_COMMANDS:
                finish_block()
        if label and not label.startswith("."):
            finish_block()
            current_global_label = label
            current_block = {
                "label": current_global_label,
                "parent_label": current_global_label,
                "line": index,
                "commands": [],
            }
        elif label and current_block is None and current_global_label:
            local_label = symbol_name_for_label(label, current_global_label=current_global_label)
            current_block = {
                "label": local_label,
                "parent_label": current_global_label,
                "line": index,
                "commands": [],
            }
        token = first_token(code)
        if not token:
            continue
        if token in script_tokens:
            if current_block is None and current_global_label:
                current_block = {
                    "label": current_global_label,
                    "parent_label": current_global_label,
                    "line": index,
                    "commands": [],
                }
            if current_block is not None:
                current_block["commands"].append(
                    {
                        "command": token,
                        "line": index,
                        "args": split_macro_args(code[len(token):]),
                    }
                )
            continue
        if current_block is not None and not current_block.get("commands") and token:
            if token in non_script_tokens:
                finish_block()
                continue
            current_block["commands"].append(
                {
                    "command": token,
                    "line": index,
                    "args": split_macro_args(code[len(token):]),
                }
            )
            continue
        if current_block is not None and current_block.get("commands"):
            current_block["commands"].append(
                {
                    "command": token,
                    "line": index,
                    "args": split_macro_args(code[len(token):]),
                }
            )
            continue
        finish_block()
    finish_block()
    return blocks


def parse_text_blocks(lines: list[str]) -> list[dict[str, Any]]:
    text_tokens = set(TEXT_LINE_MACROS) | set(TEXT_TERMINATOR_MACROS) | set(TEXT_COMMAND_SPECS)
    text_start_tokens = {"text", "text_start", "text_ram", "text_bcd", "text_move"}
    blocks: list[dict[str, Any]] = []
    current_global_label = ""
    current_block: dict[str, Any] | None = None

    def finish_block() -> None:
        nonlocal current_block
        if current_block and current_block.get("commands"):
            blocks.append(current_block)
        current_block = None

    for index, raw_line in enumerate(lines, start=1):
        clean = strip_comment(raw_line).strip()
        if not clean:
            continue
        label, code = split_label(clean)
        if label and not label.startswith("."):
            finish_block()
            current_global_label = label
            current_block = {
                "label": current_global_label,
                "line": index,
                "commands": [],
            }
        elif label and current_block is None and current_global_label:
            local_label = symbol_name_for_label(label, current_global_label=current_global_label)
            current_block = {
                "label": local_label,
                "line": index,
                "commands": [],
            }
        token = first_token(code)
        if not token:
            continue
        if token in text_tokens:
            if current_block is None and current_global_label:
                if token not in text_start_tokens:
                    continue
                current_block = {
                    "label": current_global_label,
                    "line": index,
                    "commands": [],
                }
            if current_block is not None:
                current_block["commands"].append(
                    {
                        "command": token,
                        "line": index,
                        "args": split_macro_args(code[len(token):]),
                    }
                )
            continue
        if current_block is not None and current_block.get("commands"):
            current_block["commands"].append(
                {
                    "command": token,
                    "line": index,
                    "args": split_macro_args(code[len(token):]),
                }
            )
            continue
        finish_block()
    finish_block()
    return blocks


def parse_movement_blocks(lines: list[str]) -> list[dict[str, Any]]:
    movement_tokens = (
        set(MOVEMENT_DIRECTIONAL_MACROS)
        | set(MOVEMENT_NO_ARG_MACROS)
        | set(MOVEMENT_U8_ARG_MACROS)
        | MOVEMENT_SPECIAL_MACROS
    )
    blocks: list[dict[str, Any]] = []
    current_global_label = ""
    current_block: dict[str, Any] | None = None

    def finish_block() -> None:
        nonlocal current_block
        if current_block and current_block.get("commands"):
            blocks.append(current_block)
        current_block = None

    for index, raw_line in enumerate(lines, start=1):
        clean = strip_comment(raw_line).strip()
        if not clean:
            continue
        label, code = split_label(clean)
        if label and not label.startswith("."):
            finish_block()
            current_global_label = label
            current_block = {
                "label": current_global_label,
                "line": index,
                "commands": [],
            }
        elif label and current_block is None and current_global_label:
            local_label = symbol_name_for_label(label, current_global_label=current_global_label)
            current_block = {
                "label": local_label,
                "line": index,
                "commands": [],
            }
        token = first_token(code)
        if not token:
            continue
        if token in movement_tokens:
            if current_block is None and current_global_label:
                current_block = {
                    "label": current_global_label,
                    "line": index,
                    "commands": [],
                }
            if current_block is not None:
                current_block["commands"].append(
                    {
                        "command": token,
                        "line": index,
                        "args": split_macro_args(code[len(token):]),
                    }
                )
            continue
        if current_block is not None and current_block.get("commands"):
            current_block["commands"].append(
                {
                    "command": token,
                    "line": index,
                    "args": split_macro_args(code[len(token):]),
                }
            )
            continue
        finish_block()
    finish_block()
    return blocks


def parse_source_constants(lines: list[str]) -> dict[str, int]:
    constants: dict[str, int] = {}
    const_value = 0
    const_inc = 1
    in_macro_definition = False

    def resolve(expr: str) -> int | None:
        local_constants = {**constants, "const_value": const_value, "const_inc": const_inc}
        return evaluate_int_expression(expr, local_constants)

    for raw_line in lines:
        clean = code_after_label(strip_comment(raw_line).strip())
        if not clean:
            continue
        token = first_token(clean)
        args = split_macro_args(clean[len(token):])
        if token == "MACRO":
            in_macro_definition = True
            continue
        if token == "ENDM":
            in_macro_definition = False
            continue
        if in_macro_definition:
            continue
        if token == "object_const_def":
            const_value = 2
            const_inc = 1
            continue
        if token == "const_def":
            value = resolve(args[0]) if args else 0
            inc = resolve(args[1]) if len(args) > 1 else 1
            const_value = 0 if value is None else value
            const_inc = 1 if inc is None else inc
            continue
        if token == "const" and args:
            constants[args[0]] = const_value
            const_value += const_inc
            continue
        if token == "const_skip":
            count = resolve(args[0]) if args else 1
            const_value += const_inc * (1 if count is None else count)
            continue
        if token == "const_next" and args:
            value = resolve(args[0])
            if value is not None:
                const_value = value
            continue
        if token == "ugdoor" and len(args) >= 3:
            door_id = args[0].strip()
            x_value = resolve(args[1])
            y_value = resolve(args[2])
            if x_value is not None:
                constants[f"UGDOOR_{door_id}_XCOORD"] = x_value
            if y_value is not None:
                constants[f"UGDOOR_{door_id}_YCOORD"] = y_value
            continue
        assign_match = DEF_ASSIGN_RE.match(clean)
        if assign_match:
            value = resolve(assign_match.group("expr"))
            if value is not None:
                name = assign_match.group("name")
                if name == "const_inc":
                    const_inc = value
                elif name == "const_value":
                    const_value = value
                else:
                    constants[name] = value
            continue
        equ_match = DEF_EQU_RE.match(clean)
        if equ_match:
            value = resolve(equ_match.group("expr"))
            if value is not None:
                constants[equ_match.group("name")] = value
            continue
    return constants


def parse_channel_blocks(lines: list[str]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    current_global_label = ""
    for index, raw_line in enumerate(lines):
        clean_line = strip_comment(raw_line).strip()
        label, code = split_label(clean_line)
        if label and not label.startswith("."):
            current_global_label = label
        clean = code.strip()
        match = CHANNEL_COUNT_RE.match(clean)
        if not match:
            continue
        expected = parse_int_literal(match.group("count"))
        channel_lines: list[int] = []
        channels: list[dict[str, Any]] = []
        for next_index in range(index + 1, len(lines)):
            next_clean = code_after_label(strip_comment(lines[next_index]).strip())
            if not next_clean:
                if channel_lines:
                    break
                continue
            channel_match = CHANNEL_RE.match(next_clean)
            if channel_match:
                channel_lines.append(next_index + 1)
                channels.append(
                    {
                        "line": next_index + 1,
                        "channel": channel_match.group("channel"),
                        "label": channel_match.group("label"),
                    }
                )
                continue
            break
        blocks.append(
            {
                "line": index + 1,
                "label": current_global_label,
                "expected": expected,
                "actual": len(channel_lines),
                "channel_lines": channel_lines,
                "channels": channels,
            }
        )
    return blocks


def count_object_constants(lines: list[str]) -> int:
    in_block = False
    count = 0
    for raw_line in lines:
        clean = code_after_label(strip_comment(raw_line).strip())
        if not clean:
            if in_block:
                break
            continue
        token = first_token(clean)
        if token == "object_const_def":
            in_block = True
            continue
        if not in_block:
            continue
        if token == "const":
            count += 1
            continue
        if token in {"const_skip", "const_next"}:
            continue
        break
    return count


def is_map_event_file(source_file: str, parsed: dict[str, Any]) -> bool:
    normalized = source_file.replace("\\", "/").lower()
    if normalized.startswith("maps/"):
        return True
    if any(str(label["label"]).endswith("_MapEvents") for label in parsed.get("global_labels", [])):
        return True
    macro_lines = parsed.get("macro_lines", {})
    return any(section in macro_lines for section in MAP_SECTION_MACROS.values())


def is_rom_mirror_invariant(item: dict[str, Any]) -> bool:
    return str(item.get("type", "")) in ROM_MIRROR_INVARIANT_TYPES


def source_commands(source_file: str) -> list[str]:
    return [
        f"python -m tools.debugger content-mirror --source-file {source_file}",
        f"python -m tools.debugger expect --source-file {source_file} --expect report-valid",
        f"python -m tools.debugger provenance --source-file {source_file}",
        f"python -m tools.debugger compare --changed-file {source_file}",
    ]


def content_invariant(
    *,
    invariant_id: str,
    invariant_type: str,
    status: str,
    severity: int,
    title: str,
    source_file: str,
    line: int = 0,
    evidence: list[str] | None = None,
    commands: list[str] | None = None,
    related_files: list[str] | None = None,
    related_symbols: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": invariant_id,
        "type": invariant_type,
        "status": status,
        "severity": int(severity),
        "title": title,
        "source_file": source_file,
        "line": int(line),
        "evidence": unique_list(evidence or []),
        "commands": unique_list(commands or []),
        "related_files": unique_list(related_files or []),
        "related_symbols": unique_list(related_symbols or []),
    }


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


def strip_comment(line: str) -> str:
    out = []
    in_quote = False
    escaped = False
    for char in line:
        if char == '"' and not escaped:
            in_quote = not in_quote
        if char == ";" and not in_quote:
            break
        out.append(char)
        escaped = char == "\\" and not escaped
    return "".join(out)


def split_label(line: str) -> tuple[str, str]:
    match = LABEL_RE.match(line)
    if match:
        return match.group("label"), line[match.end():].strip()
    match = LOCAL_LABEL_ONLY_RE.match(line)
    if match:
        return match.group("label"), ""
    return "", line.strip()


def code_after_label(line: str) -> str:
    return split_label(line)[1]


def symbol_name_for_label(label: str, *, current_global_label: str) -> str:
    if label.startswith(".") and current_global_label:
        return f"{current_global_label}{label}"
    return label


def first_token(line: str) -> str:
    match = TOKEN_RE.match(line.strip())
    return match.group("token") if match else ""


def parse_incbin_entries(code: str, *, equs_macros: dict[str, str] | None = None) -> list[dict[str, Any]]:
    match = INCBIN_ARGS_RE.search(code.strip())
    if not match:
        return []
    args = split_macro_args(match.group("args"))
    if not args:
        return []
    aliases = equs_macros or {}
    if len(args) == 2 and args[1].strip() in aliases:
        args = [args[0], *split_macro_args(aliases[args[1].strip()])]
    path = args[0].strip()
    if len(path) < 2 or not path.startswith('"') or not path.endswith('"'):
        return []
    return [{"path": path[1:-1], "args": args}]


def parse_int_literal(value: str) -> int:
    text = value.strip()
    if text.startswith("$"):
        return int(text[1:], 16)
    if text.lower().startswith("0x"):
        return int(text, 16)
    return int(text)


def unique_list(values: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value)
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def dict_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list | tuple):
        return [item for item in value if isinstance(item, dict)]
    return []
