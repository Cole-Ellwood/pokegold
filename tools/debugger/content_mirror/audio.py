"""Audio channel headers: source-shape invariants + ROM-byte comparison."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from .helpers import (
    code_after_label,
    content_invariant,
    dict_items,
    evaluate_int_expression,
    first_mismatch,
    format_optional_byte,
    hex_window,
    parse_int_literal,
    source_commands,
    split_label,
    strip_comment,
    unique_list,
)


CHANNEL_COUNT_RE = re.compile(r"^channel_count\s+(?P<count>[$0-9A-Fa-fx]+)\b")
CHANNEL_RE = re.compile(r"^channel\s+(?P<channel>[$0-9A-Fa-fx]+)\s*,\s*(?P<label>[A-Za-z_.$][A-Za-z0-9_.$]*)")


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
