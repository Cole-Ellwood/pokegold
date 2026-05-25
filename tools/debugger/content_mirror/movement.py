"""Movement-data bytecode: ROM-byte comparison + parser."""

from __future__ import annotations

import hashlib
from typing import Any

from .helpers import (
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
