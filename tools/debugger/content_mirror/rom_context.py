"""Built-ROM and symbol-table loaders shared by every content-type comparator."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ..provenance import display_path, resolve_path
from .helpers import (
    DEF_ASSIGN_RE,
    DEF_EQU_RE,
    DEF_EQUS_RE,
    SYM_CONSTANT_RE,
    SYM_LABEL_RE,
    code_after_label,
    evaluate_int_expression,
    first_token,
    split_macro_args,
    strip_comment,
)


DEFAULT_ROM_PATH = "pokegold.gbc"
DEFAULT_SYMBOLS_PATH = "pokegold.sym"
MAP_EVENT_ENTRY_SIZES = {
    "warp_event": 5,
    "coord_event": 8,
    "bg_event": 5,
    "object_event": 13,
}
CHARMAP_RE = re.compile(r'^\s*charmap\s+"(?P<token>(?:\\.|[^"])*)"\s*,\s*(?P<value>[^;\s]+)')


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
