"""Map-event tables: source invariants + ROM-byte comparison."""

from __future__ import annotations

import hashlib
from typing import Any

from .helpers import (
    append_count,
    code_after_label,
    content_invariant,
    evaluate_int_expression,
    first_mismatch,
    first_token,
    format_optional_byte,
    hex_window,
    padded_fields,
    source_commands,
    split_label,
    split_macro_args,
    strip_comment,
    unique_list,
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


def is_map_event_file(source_file: str, parsed: dict[str, Any]) -> bool:
    normalized = source_file.replace("\\", "/").lower()
    if normalized.startswith("maps/"):
        return True
    if any(str(label["label"]).endswith("_MapEvents") for label in parsed.get("global_labels", [])):
        return True
    macro_lines = parsed.get("macro_lines", {})
    return any(section in macro_lines for section in MAP_SECTION_MACROS.values())


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
