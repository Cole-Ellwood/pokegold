"""Text-macro blocks: ROM-byte comparison + parser for ``parse_rgbds_source``."""

from __future__ import annotations

import hashlib
from typing import Any

from .charmap import append_charmap_token, encode_charmap_string, expand_rgbds_string_formats
from .helpers import (
    content_invariant,
    dict_items,
    evaluate_int_expression,
    first_mismatch,
    first_token,
    format_optional_byte,
    hex_window,
    is_quoted_rgbds_string,
    split_label,
    split_macro_args,
    strip_comment,
    symbol_name_for_label,
    unique_list,
)


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
