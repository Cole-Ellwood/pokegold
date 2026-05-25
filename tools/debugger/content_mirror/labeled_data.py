"""Labeled db/dw/dn data blocks: ROM-byte comparison + encoder."""

from __future__ import annotations

import hashlib
from typing import Any

from .charmap import append_charmap_token, encode_charmap_string, expand_rgbds_string_formats
from .helpers import (
    DATA_STRING_CONTINUATION_DIRECTIVES,
    content_invariant,
    dict_items,
    evaluate_int_expression,
    first_mismatch,
    format_optional_byte,
    hex_window,
    is_quoted_rgbds_string,
    unique_list,
)
from .text import TEXT_LINE_MACROS


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
