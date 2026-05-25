"""Script command bytecode: parser + ROM-byte comparison + encoder.

The declarative spec tables live in :mod:`.scripts_data`.
"""

from __future__ import annotations

import hashlib
from typing import Any

from .helpers import (
    DATA_BYTE_DIRECTIVES,
    content_invariant,
    dict_items,
    evaluate_int_expression,
    first_mismatch,
    first_token,
    format_optional_byte,
    hex_window,
    split_label,
    split_macro_args,
    strip_comment,
    symbol_name_for_label,
    unique_list,
)
from .movement import (
    MOVEMENT_DIRECTIONAL_MACROS,
    MOVEMENT_NO_ARG_MACROS,
    MOVEMENT_SPECIAL_MACROS,
    MOVEMENT_U8_ARG_MACROS,
)
from .scripts_data import (
    NON_SCRIPT_BLOCK_START_TOKENS,
    SCRIPT_COMMAND_SPECS,
    SCRIPT_DATA_MACRO_SPECS,
    SCRIPT_TERMINAL_COMMANDS,
)


def script_symbol_name(label: str, *, block_label: str) -> str:
    if label.startswith(".") and block_label:
        return f"{block_label}{label}"
    return label


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
