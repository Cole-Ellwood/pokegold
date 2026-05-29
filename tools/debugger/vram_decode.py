from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Mapping


VRAM_SIZE = 0x2000
TILEMAP_WIDTH = 32
TILEMAP_HEIGHT = 32
TILEMAP_CELL_COUNT = TILEMAP_WIDTH * TILEMAP_HEIGHT
TILEMAP_A_OFFSET = 0x1800
TILEMAP_B_OFFSET = 0x1C00
OAM_ENTRY_COUNT = 40
OAM_ENTRY_SIZE = 4
OAM_SIZE = OAM_ENTRY_COUNT * OAM_ENTRY_SIZE

DMG_SHADE_NAMES = ("white", "light_gray", "dark_gray", "black")

IO_REGISTER_ALIASES = {
    "rLCDC": 0xFF40,
    "LCDC": 0xFF40,
    "FF40": 0xFF40,
    "rSTAT": 0xFF41,
    "STAT": 0xFF41,
    "FF41": 0xFF41,
    "rSCY": 0xFF42,
    "SCY": 0xFF42,
    "FF42": 0xFF42,
    "rSCX": 0xFF43,
    "SCX": 0xFF43,
    "FF43": 0xFF43,
    "rBGP": 0xFF47,
    "BGP": 0xFF47,
    "FF47": 0xFF47,
    "rOBP0": 0xFF48,
    "OBP0": 0xFF48,
    "FF48": 0xFF48,
    "rOBP1": 0xFF49,
    "OBP1": 0xFF49,
    "FF49": 0xFF49,
    "rWY": 0xFF4A,
    "WY": 0xFF4A,
    "FF4A": 0xFF4A,
    "rWX": 0xFF4B,
    "WX": 0xFF4B,
    "FF4B": 0xFF4B,
    "rVBK": 0xFF4F,
    "VBK": 0xFF4F,
    "FF4F": 0xFF4F,
}

IO_REGISTER_NAMES = {
    0xFF40: "rLCDC",
    0xFF41: "rSTAT",
    0xFF42: "rSCY",
    0xFF43: "rSCX",
    0xFF47: "rBGP",
    0xFF48: "rOBP0",
    0xFF49: "rOBP1",
    0xFF4A: "rWY",
    0xFF4B: "rWX",
    0xFF4F: "rVBK",
}


def decode_vram_state(
    vram0: bytes | bytearray,
    *,
    vram1: bytes | bytearray | None = None,
    oam: bytes | bytearray = b"",
    io_registers: Mapping[Any, Any] | None = None,
) -> dict[str, Any]:
    bank0 = require_bytes("vram0", vram0, VRAM_SIZE)
    bank1 = require_bytes("vram1", vram1, VRAM_SIZE) if vram1 is not None else None
    oam_bytes = bytes(oam)
    if oam_bytes and len(oam_bytes) < OAM_SIZE:
        raise ValueError(f"oam must be at least {OAM_SIZE} bytes, got {len(oam_bytes)}")
    normalized_io = normalize_io_registers(io_registers or {})
    lcdc = normalized_io.get(0xFF40, 0)
    stat = normalized_io.get(0xFF41, 0)
    vbk = normalized_io.get(0xFF4F, 0)
    lcd = decode_lcdc_state(lcdc, stat, normalized_io)
    tilemaps = {
        "9800": decode_tilemap(
            bank0,
            attr_vram=bank1,
            base_address=0x9800,
            offset=TILEMAP_A_OFFSET,
            selected_for_bg=lcd["bg_tilemap"] == "9800",
            selected_for_window=lcd["window_tilemap"] == "9800",
        ),
        "9C00": decode_tilemap(
            bank0,
            attr_vram=bank1,
            base_address=0x9C00,
            offset=TILEMAP_B_OFFSET,
            selected_for_bg=lcd["bg_tilemap"] == "9C00",
            selected_for_window=lcd["window_tilemap"] == "9C00",
        ),
    }
    oam_entries = decode_oam_entries(oam_bytes[:OAM_SIZE], sprite_size=lcd["sprite_size"]) if oam_bytes else []
    return {
        "schema_version": 1,
        "kind": "unified_debugger_vram_decode",
        "proof_status": "decoded_snapshot",
        "hardware_behavior_proven": False,
        "hardware_proof_boundary": "Structured decode of captured VRAM/OAM/IO bytes; not pixel-accurate PPU rendering proof.",
        "vram": {
            "bank0_size": len(bank0),
            "bank1_present": bank1 is not None,
            "bank1_size": 0 if bank1 is None else len(bank1),
            "active_vram_bank": vbk & 0x01,
            "active_vram_bank_raw": vbk,
            "active_vram_bank_raw_hex": f"{vbk:02X}",
        },
        "io_registers": {
            IO_REGISTER_NAMES[address]: f"{value:02X}"
            for address, value in sorted(normalized_io.items())
            if address in IO_REGISTER_NAMES
        },
        "lcd_state": lcd,
        "palettes": {
            "dmg": {
                "bgp": decode_dmg_palette(normalized_io.get(0xFF47, 0), "BGP", transparent_zero=False),
                "obp0": decode_dmg_palette(normalized_io.get(0xFF48, 0), "OBP0", transparent_zero=True),
                "obp1": decode_dmg_palette(normalized_io.get(0xFF49, 0), "OBP1", transparent_zero=True),
            }
        },
        "tilemaps": tilemaps,
        "oam": {
            "entry_count": len(oam_entries),
            "visible_guess_count": sum(1 for entry in oam_entries if entry["visible_guess"]),
            "entries": oam_entries,
        },
    }


def require_bytes(name: str, data: bytes | bytearray | None, size: int) -> bytes:
    if data is None:
        raise ValueError(f"{name} is required")
    out = bytes(data)
    if len(out) != size:
        raise ValueError(f"{name} must be exactly {size} bytes, got {len(out)}")
    return out


def normalize_io_registers(io_registers: Mapping[Any, Any]) -> dict[int, int]:
    normalized: dict[int, int] = {}
    for raw_key, raw_value in io_registers.items():
        address = normalize_io_key(raw_key)
        if address is None:
            continue
        normalized[address] = normalize_byte(raw_value)
    return normalized


def normalize_io_key(raw_key: Any) -> int | None:
    if isinstance(raw_key, int):
        return raw_key & 0xFFFF
    text = str(raw_key).strip()
    if text in IO_REGISTER_ALIASES:
        return IO_REGISTER_ALIASES[text]
    if text.startswith("$"):
        text = text[1:]
    try:
        value = int(text, 16)
    except ValueError:
        return None
    return value & 0xFFFF


def normalize_byte(raw_value: Any) -> int:
    if isinstance(raw_value, str):
        text = raw_value.strip()
        if text.startswith("$"):
            text = text[1:]
        return int(text, 16) & 0xFF
    return int(raw_value) & 0xFF


def decode_lcdc_state(lcdc: int, stat: int, io_registers: Mapping[int, int]) -> dict[str, Any]:
    return {
        "lcdc": lcdc,
        "lcdc_hex": f"{lcdc:02X}",
        "stat": stat,
        "stat_hex": f"{stat:02X}",
        "lcd_enabled": bool(lcdc & 0x80),
        "window_tilemap": "9C00" if lcdc & 0x40 else "9800",
        "window_enabled": bool(lcdc & 0x20),
        "bg_window_tile_data": "8000" if lcdc & 0x10 else "8800",
        "bg_tilemap": "9C00" if lcdc & 0x08 else "9800",
        "sprite_size": "8x16" if lcdc & 0x04 else "8x8",
        "sprites_enabled": bool(lcdc & 0x02),
        "bg_window_enabled_or_priority": bool(lcdc & 0x01),
        "ppu_mode": stat & 0x03,
        "scroll": {
            "scx": io_registers.get(0xFF43, 0),
            "scy": io_registers.get(0xFF42, 0),
            "wx": io_registers.get(0xFF4B, 0),
            "wy": io_registers.get(0xFF4A, 0),
        },
    }


def decode_dmg_palette(raw: int, name: str, *, transparent_zero: bool) -> dict[str, Any]:
    entries = []
    for color_id in range(4):
        shade = (raw >> (color_id * 2)) & 0x03
        entries.append(
            {
                "color_id": color_id,
                "shade": shade,
                "shade_name": DMG_SHADE_NAMES[shade],
                "transparent": transparent_zero and color_id == 0,
            }
        )
    return {"name": name, "raw": raw, "raw_hex": f"{raw:02X}", "entries": entries}


def decode_tilemap(
    vram: bytes,
    *,
    attr_vram: bytes | None,
    base_address: int,
    offset: int,
    selected_for_bg: bool,
    selected_for_window: bool,
) -> dict[str, Any]:
    cells: list[dict[str, Any]] = []
    for index in range(TILEMAP_CELL_COUNT):
        row = index // TILEMAP_WIDTH
        col = index % TILEMAP_WIDTH
        value = vram[offset + index]
        attr = attr_vram[offset + index] if attr_vram is not None else None
        cell = {
            "row": row,
            "col": col,
            "address": f"{base_address + index:04X}",
            "offset": f"{offset + index:04X}",
            "tile_index": value,
            "tile_hex": f"{value:02X}",
        }
        if attr is not None:
            cell["attributes"] = decode_bg_attributes(attr)
        cells.append(cell)
    tile_counts = Counter(cell["tile_index"] for cell in cells)
    return {
        "base_address": f"{base_address:04X}",
        "offset": f"{offset:04X}",
        "width": TILEMAP_WIDTH,
        "height": TILEMAP_HEIGHT,
        "selected_for_bg": selected_for_bg,
        "selected_for_window": selected_for_window,
        "unique_tile_count": len(tile_counts),
        "nonzero_count": sum(1 for cell in cells if cell["tile_index"]),
        "top_tiles": [
            {"tile_index": tile, "tile_hex": f"{tile:02X}", "count": count}
            for tile, count in tile_counts.most_common(8)
        ],
        "cells": cells,
    }


def decode_bg_attributes(raw: int) -> dict[str, Any]:
    return {
        "raw": raw,
        "raw_hex": f"{raw:02X}",
        "priority": bool(raw & 0x80),
        "y_flip": bool(raw & 0x40),
        "x_flip": bool(raw & 0x20),
        "vram_bank": 1 if raw & 0x08 else 0,
        "cgb_palette": raw & 0x07,
    }


def decode_oam_entries(oam: bytes, *, sprite_size: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    is_8x16 = sprite_size == "8x16"
    for index in range(OAM_ENTRY_COUNT):
        base = index * OAM_ENTRY_SIZE
        y_raw, x_raw, tile, attr = oam[base : base + OAM_ENTRY_SIZE]
        hidden_by_y = y_raw == 0 or y_raw >= 160
        hidden_by_x = x_raw == 0 or x_raw >= 168
        entries.append(
            {
                "index": index,
                "address": f"{0xFE00 + base:04X}",
                "raw_hex": bytes((y_raw, x_raw, tile, attr)).hex().upper(),
                "y_raw": y_raw,
                "x_raw": x_raw,
                "screen_y": y_raw - 16,
                "screen_x": x_raw - 8,
                "tile_index": tile,
                "tile_hex": f"{tile:02X}",
                "effective_tile_index": tile & 0xFE if is_8x16 else tile,
                "effective_tile_hex": f"{(tile & 0xFE if is_8x16 else tile):02X}",
                "attributes": decode_oam_attributes(attr),
                "hidden_by_y": hidden_by_y,
                "hidden_by_x": hidden_by_x,
                "visible_guess": not hidden_by_y and not hidden_by_x,
            }
        )
    return entries


def decode_oam_attributes(raw: int) -> dict[str, Any]:
    return {
        "raw": raw,
        "raw_hex": f"{raw:02X}",
        "bg_window_over_obj": bool(raw & 0x80),
        "y_flip": bool(raw & 0x40),
        "x_flip": bool(raw & 0x20),
        "dmg_palette": "OBP1" if raw & 0x10 else "OBP0",
        "vram_bank": 1 if raw & 0x08 else 0,
        "cgb_palette": raw & 0x07,
    }


def diff_vram_states(before: Mapping[str, Any], after: Mapping[str, Any]) -> dict[str, Any]:
    tilemap_deltas = diff_tilemaps(before.get("tilemaps", {}), after.get("tilemaps", {}))
    oam_deltas = diff_oam(before.get("oam", {}), after.get("oam", {}))
    palette_deltas = diff_palettes(before.get("palettes", {}), after.get("palettes", {}))
    lcd_deltas = diff_mapping(before.get("lcd_state", {}), after.get("lcd_state", {}), prefix=())
    scenario_flags = scenario_flags_for_diff(tilemap_deltas, oam_deltas, palette_deltas, lcd_deltas)
    return {
        "schema_version": 1,
        "kind": "unified_debugger_vram_diff",
        "proof_status": "decoded_snapshot_diff",
        "hardware_behavior_proven": False,
        "hardware_proof_boundary": "Structured diff of decoded snapshots; not pixel-accurate PPU rendering proof.",
        "tilemap_changed_cell_count": sum(delta["changed_cell_count"] for delta in tilemap_deltas),
        "tilemap_deltas": tilemap_deltas,
        "oam_changed_count": len(oam_deltas),
        "oam_deltas": oam_deltas,
        "palette_changed_count": len(palette_deltas),
        "palette_deltas": palette_deltas,
        "lcd_changed_count": len(lcd_deltas),
        "lcd_deltas": lcd_deltas,
        "scenario_flags": scenario_flags,
    }


def diff_tilemaps(before_maps: Mapping[str, Any], after_maps: Mapping[str, Any]) -> list[dict[str, Any]]:
    deltas: list[dict[str, Any]] = []
    for name in sorted(set(before_maps) | set(after_maps)):
        before_map = before_maps.get(name)
        after_map = after_maps.get(name)
        if before_map is None or after_map is None:
            deltas.append({"tilemap": name, "change_kind": "appeared" if after_map else "disappeared", "changed_cell_count": 0, "changed_cells": []})
            continue
        changed_cells = diff_tilemap_cells(before_map.get("cells", []), after_map.get("cells", []))
        if not changed_cells:
            continue
        deltas.append(
            {
                "tilemap": name,
                "change_kind": "changed",
                "base_address": before_map.get("base_address", name),
                "changed_cell_count": len(changed_cells),
                "changed_cells": changed_cells,
                "tile_position_changes": tile_position_changes(before_map.get("cells", []), after_map.get("cells", [])),
            }
        )
    return deltas


def diff_tilemap_cells(before_cells: list[Mapping[str, Any]], after_cells: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    changed: list[dict[str, Any]] = []
    for before, after in zip(before_cells, after_cells):
        before_attr = before.get("attributes", {})
        after_attr = after.get("attributes", {})
        if before.get("tile_index") == after.get("tile_index") and before_attr == after_attr:
            continue
        changed.append(
            {
                "row": before.get("row"),
                "col": before.get("col"),
                "address": before.get("address"),
                "before_tile": before.get("tile_hex"),
                "after_tile": after.get("tile_hex"),
                "before_attr": before_attr.get("raw_hex", ""),
                "after_attr": after_attr.get("raw_hex", ""),
            }
        )
    return changed


def tile_position_changes(before_cells: list[Mapping[str, Any]], after_cells: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    before_positions = positions_by_tile(before_cells)
    after_positions = positions_by_tile(after_cells)
    moves: list[dict[str, Any]] = []
    for tile in sorted(set(before_positions) | set(after_positions)):
        before_set = before_positions.get(tile, [])
        after_set = after_positions.get(tile, [])
        if before_set == after_set:
            continue
        moves.append(
            {
                "tile_index": tile,
                "tile_hex": f"{tile:02X}",
                "before_positions": before_set[:8],
                "after_positions": after_set[:8],
                "before_count": len(before_set),
                "after_count": len(after_set),
            }
        )
    return moves[:32]


def positions_by_tile(cells: list[Mapping[str, Any]]) -> dict[int, list[dict[str, int]]]:
    positions: dict[int, list[dict[str, int]]] = defaultdict(list)
    for cell in cells:
        positions[int(cell.get("tile_index", 0))].append({"row": int(cell.get("row", 0)), "col": int(cell.get("col", 0))})
    return dict(positions)


def diff_oam(before_oam: Mapping[str, Any], after_oam: Mapping[str, Any]) -> list[dict[str, Any]]:
    before_entries = {entry["index"]: entry for entry in before_oam.get("entries", [])}
    after_entries = {entry["index"]: entry for entry in after_oam.get("entries", [])}
    deltas: list[dict[str, Any]] = []
    for index in sorted(set(before_entries) | set(after_entries)):
        before = before_entries.get(index)
        after = after_entries.get(index)
        if before is None or after is None:
            deltas.append({"index": index, "change_kind": "appeared" if after else "disappeared"})
            continue
        if before.get("raw_hex") == after.get("raw_hex"):
            continue
        if not before.get("visible_guess") and after.get("visible_guess"):
            change_kind = "appeared"
        elif before.get("visible_guess") and not after.get("visible_guess"):
            change_kind = "disappeared"
        else:
            change_kind = "changed"
        deltas.append(
            {
                "index": index,
                "change_kind": change_kind,
                "before_raw": before.get("raw_hex"),
                "after_raw": after.get("raw_hex"),
                "before": compact_oam_entry(before),
                "after": compact_oam_entry(after),
            }
        )
    return deltas


def compact_oam_entry(entry: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "screen_x": entry.get("screen_x"),
        "screen_y": entry.get("screen_y"),
        "tile_hex": entry.get("tile_hex"),
        "effective_tile_hex": entry.get("effective_tile_hex"),
        "attr_hex": entry.get("attributes", {}).get("raw_hex", ""),
        "visible_guess": entry.get("visible_guess"),
    }


def diff_palettes(before_palettes: Mapping[str, Any], after_palettes: Mapping[str, Any]) -> list[dict[str, Any]]:
    deltas: list[dict[str, Any]] = []
    before_dmg = before_palettes.get("dmg", {})
    after_dmg = after_palettes.get("dmg", {})
    if isinstance(before_dmg, Mapping) and isinstance(after_dmg, Mapping):
        for palette_id in sorted(set(before_dmg) | set(after_dmg)):
            before_palette = before_dmg.get(palette_id, {})
            after_palette = after_dmg.get(palette_id, {})
            if not isinstance(before_palette, Mapping) or not isinstance(after_palette, Mapping):
                if before_palette != after_palette:
                    deltas.append(
                        {
                            "palette": f"dmg.{palette_id}",
                            "change_kind": "palette_record_changed",
                            "before": before_palette,
                            "after": after_palette,
                        }
                    )
                continue
            before_entries = {entry["color_id"]: entry for entry in before_palette.get("entries", [])}
            after_entries = {entry["color_id"]: entry for entry in after_palette.get("entries", [])}
            for color_id in sorted(set(before_entries) | set(after_entries)):
                before_entry = before_entries.get(color_id)
                after_entry = after_entries.get(color_id)
                if before_entry == after_entry:
                    continue
                deltas.append(
                    {
                        "palette": f"dmg.{palette_id}",
                        "change_kind": "color_index_shift",
                        "color_id": color_id,
                        "before_shade": None if before_entry is None else before_entry.get("shade"),
                        "after_shade": None if after_entry is None else after_entry.get("shade"),
                        "before_shade_name": "" if before_entry is None else before_entry.get("shade_name", ""),
                        "after_shade_name": "" if after_entry is None else after_entry.get("shade_name", ""),
                        "before_raw": before_palette.get("raw_hex", ""),
                        "after_raw": after_palette.get("raw_hex", ""),
                    }
                )
    known_top = {"dmg"}
    extra_before = {key: value for key, value in before_palettes.items() if key not in known_top}
    extra_after = {key: value for key, value in after_palettes.items() if key not in known_top}
    deltas.extend(diff_mapping(extra_before, extra_after, prefix=()))
    return deltas


def diff_mapping(before: Mapping[str, Any], after: Mapping[str, Any], *, prefix: tuple[str, ...]) -> list[dict[str, Any]]:
    deltas: list[dict[str, Any]] = []
    for key in sorted(set(before) | set(after)):
        before_value = before.get(key)
        after_value = after.get(key)
        path = (*prefix, str(key))
        if isinstance(before_value, Mapping) and isinstance(after_value, Mapping):
            deltas.extend(diff_mapping(before_value, after_value, prefix=path))
        elif before_value != after_value:
            deltas.append({"path": ".".join(path), "before": before_value, "after": after_value})
    return deltas


def scenario_flags_for_diff(
    tilemap_deltas: list[dict[str, Any]],
    oam_deltas: list[dict[str, Any]],
    palette_deltas: list[dict[str, Any]],
    lcd_deltas: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    flags: list[dict[str, Any]] = []
    if tilemap_deltas and not oam_deltas:
        flags.append(
            {
                "id": "tilemap_changed_oam_stable",
                "surface": "bg_tilemap",
                "reason": "Tilemap cells changed while OAM entries stayed byte-identical; this matches the VBA tile-jumble symptom shape where sprites remain stable.",
            }
        )
    if tilemap_deltas and not palette_deltas and not lcd_deltas:
        flags.append(
            {
                "id": "tile_indices_changed_without_palette_or_lcdc_shift",
                "surface": "bg_tilemap",
                "reason": "Tilemap indices changed without decoded DMG palette or LCDC state changes.",
            }
        )
    return flags
