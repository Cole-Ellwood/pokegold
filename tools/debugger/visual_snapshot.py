from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from tools.trace import runtime as trace_runtime

from .catalog import ROOT
from .ingest import sha256_file
from .provenance import display_path, parse_symbol_table, resolve_path
from .workflow import command_is_runnable


DEFAULT_ROM = "pokegold.gbc"
DEFAULT_SYMBOLS = "pokegold.sym"
DEFAULT_SYMBOL_SURFACES = {
    "wTilemap": 20 * 18,
    "wAttrmap": 20 * 18,
    "wShadowOAM": 40 * 4,
    "hBGMapMode": 1,
    "hBGMapAddress": 2,
}
IO_REGISTERS = {
    "rLCDC": 0xFF40,
    "rSTAT": 0xFF41,
    "rSCY": 0xFF42,
    "rSCX": 0xFF43,
    "rLY": 0xFF44,
    "rLYC": 0xFF45,
    "rDMA": 0xFF46,
    "rBGP": 0xFF47,
    "rOBP0": 0xFF48,
    "rOBP1": 0xFF49,
    "rWY": 0xFF4A,
    "rWX": 0xFF4B,
    "rVBK": 0xFF4F,
    "rSVBK": 0xFF70,
}


def build_visual_snapshot_report(
    *,
    rom_path: str = DEFAULT_ROM,
    symbols_path: str = DEFAULT_SYMBOLS,
    save_state: str = "",
    frames: int = 0,
    execute: bool = False,
    max_bytes: int = 512,
    root: Path = ROOT,
) -> dict[str, Any]:
    rom = resolve_path(rom_path, root=root)
    sym = resolve_path(symbols_path, root=root)
    save = resolve_path(save_state, root=root) if save_state else None
    errors: list[str] = []
    warnings: list[str] = []
    if frames < 0:
        errors.append("--frames must be non-negative")
    if max_bytes < 1:
        errors.append("--max-bytes must be positive")
    if not rom.exists():
        errors.append(f"missing ROM: {rom_path}")
    if not sym.exists():
        errors.append(f"missing symbols: {symbols_path}")
    if execute and not save_state:
        errors.append("--execute requires --save-state")
    if save is not None and not save.exists():
        errors.append(f"missing save-state: {save_state}")

    symbol_table = parse_symbol_table(sym) if sym.exists() else {}
    planned_surfaces = planned_symbol_surfaces(symbol_table)
    commands = visual_snapshot_commands(
        rom_path=rom_path,
        symbols_path=symbols_path,
        save_state=save_state,
        frames=frames,
    )
    report = {
        "schema_version": 1,
        "kind": "unified_debugger_visual_snapshot",
        "root": str(root),
        "valid": not errors,
        "proof_status": "runtime_observed" if execute and not errors else "planned_only",
        "executed": execute and not errors,
        "rom": display_path(rom, root=root),
        "rom_sha256": sha256_file(rom) if rom.exists() else "",
        "symbols": display_path(sym, root=root),
        "symbols_sha256": sha256_file(sym) if sym.exists() else "",
        "save_state": display_path(save, root=root) if save is not None else "",
        "frames": frames,
        "max_bytes": max_bytes,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "planned_surface_count": len(planned_surfaces),
        "planned_surfaces": planned_surfaces,
        "surface_count": 0,
        "surfaces": [],
        "io_registers": {},
        "lcd_state": {},
        "screen_frame_count": 0,
        "screen_frame": {},
        "framebuffer": "",
        "command_count": len(commands),
        "commands": commands,
        "runnable_commands": [command for command in commands if command_is_runnable(command)],
        "blocked_commands": [command for command in commands if not command_is_runnable(command)],
        "known_limits": [
            "This captures CPU-visible visual/UI state and a framebuffer digest/sample when PyBoy exposes screen data at a bounded runtime point; it is not a pixel-accurate PPU mirror.",
            "VRAM/OAM reads are snapshots and may reflect emulator memory access semantics rather than hardware bus restrictions during LCD modes.",
            "Use effect traces or dynamic taint to prove which instruction wrote a visual surface after a snapshot differs from expectation.",
        ],
    }
    if errors or not execute:
        return report

    snapshot = execute_visual_snapshot(
        rom=rom,
        save_state=save,
        frames=frames,
        symbol_table=symbol_table,
        max_bytes=max_bytes,
    )
    report.update(snapshot)
    return report


def planned_symbol_surfaces(symbol_table: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    surfaces: list[dict[str, Any]] = []
    for symbol, size in DEFAULT_SYMBOL_SURFACES.items():
        entry = symbol_table.get(symbol)
        surfaces.append(
            {
                "kind": "symbol_surface",
                "symbol": symbol,
                "found": bool(entry),
                "bank": entry.get("bank_hex", "") if entry else "",
                "address": entry.get("address_hex", "") if entry else "",
                "size": size,
            }
        )
    surfaces.append({"kind": "hardware_surface", "symbol": "OAM", "found": True, "address": "FE00", "size": 40 * 4})
    surfaces.append({"kind": "hardware_surface", "symbol": "VRAM0", "found": True, "address": "8000", "bank": "00", "size": 0x2000})
    surfaces.append({"kind": "hardware_surface", "symbol": "VRAM1", "found": True, "address": "8000", "bank": "01", "size": 0x2000})
    return surfaces


def execute_visual_snapshot(
    *,
    rom: Path,
    save_state: Path | None,
    frames: int,
    symbol_table: dict[str, dict[str, Any]],
    max_bytes: int,
) -> dict[str, Any]:
    pyboy = trace_runtime.open_pyboy(
        rom,
        "PyBoy is required for visual snapshot capture. Import failed",
    )
    trace_runtime.disable_realtime(pyboy)
    try:
        if save_state is not None:
            with save_state.open("rb") as fh:
                pyboy.load_state(fh)
        for _ in range(frames):
            pyboy.tick(1, False, False)
        io_registers = {
            name: f"{read_byte(pyboy, address):02X}"
            for name, address in IO_REGISTERS.items()
        }
        surfaces = [
            *symbol_surface_snapshots(pyboy, symbol_table=symbol_table, max_bytes=max_bytes),
            surface_snapshot(pyboy, kind="hardware_surface", name="OAM", address=0xFE00, size=40 * 4, max_bytes=max_bytes),
            surface_snapshot(pyboy, kind="hardware_surface", name="VRAM0", address=0x8000, size=0x2000, bank=0, max_bytes=max_bytes),
            surface_snapshot(pyboy, kind="hardware_surface", name="VRAM1", address=0x8000, size=0x2000, bank=1, max_bytes=max_bytes),
        ]
        screen_frame = screen_frame_snapshot(pyboy, frame=frames, max_bytes=max_bytes)
        snapshot = {
            "surface_count": len(surfaces),
            "surfaces": surfaces,
            "io_registers": io_registers,
            "lcd_state": lcd_state(io_registers),
        }
        if screen_frame:
            snapshot.update(
                {
                    "screen_frame_count": 1,
                    "screen_frame": screen_frame,
                    "framebuffer": screen_frame["framebuffer"],
                }
            )
        return snapshot
    finally:
        try:
            pyboy.stop(save=False)
        except TypeError:
            pyboy.stop()


def symbol_surface_snapshots(
    pyboy: Any,
    *,
    symbol_table: dict[str, dict[str, Any]],
    max_bytes: int,
) -> list[dict[str, Any]]:
    surfaces: list[dict[str, Any]] = []
    for symbol, size in DEFAULT_SYMBOL_SURFACES.items():
        entry = symbol_table.get(symbol)
        if not entry:
            continue
        surfaces.append(
            surface_snapshot(
                pyboy,
                kind="symbol_surface",
                name=symbol,
                address=int(entry["address"]),
                size=size,
                bank=int(entry["bank"]),
                max_bytes=max_bytes,
            )
        )
    return surfaces


def surface_snapshot(
    pyboy: Any,
    *,
    kind: str,
    name: str,
    address: int,
    size: int,
    max_bytes: int,
    bank: int | None = None,
) -> dict[str, Any]:
    data, bank_read = read_memory_range(pyboy, address=address, size=size, bank=bank)
    sample = data[:max_bytes]
    return {
        "kind": kind,
        "name": name,
        "address": f"{address & 0xFFFF:04X}",
        "bank": "" if bank is None else f"{bank & 0xFF:02X}",
        "bank_read": bank_read,
        "size": size,
        "sha256": hashlib.sha256(bytes(data)).hexdigest(),
        "nonzero_count": sum(1 for value in data if value),
        "unique_byte_count": len(set(data)),
        "sample_size": len(sample),
        "sample_hex": bytes(sample).hex().upper(),
        "truncated": len(sample) < len(data),
    }


def read_memory_range(pyboy: Any, *, address: int, size: int, bank: int | None = None) -> tuple[list[int], str]:
    if bank is None:
        return ([read_byte(pyboy, (address + offset) & 0xFFFF) for offset in range(size)], "unbanked")
    try:
        return (
            [
                int(pyboy.memory[bank, (address + offset) & 0xFFFF]) & 0xFF
                for offset in range(size)
            ],
            "exact",
        )
    except Exception:
        return ([read_byte(pyboy, (address + offset) & 0xFFFF) for offset in range(size)], "fallback_unbanked")


def read_byte(pyboy: Any, address: int) -> int:
    return int(pyboy.memory[address]) & 0xFF


def screen_frame_snapshot(pyboy: Any, *, frame: int, max_bytes: int) -> dict[str, Any]:
    screen_data = read_screen_data(pyboy)
    if not screen_data:
        return {}
    data = bytes(screen_data["data"])
    sample = data[:max_bytes]
    digest = hashlib.sha256(data).hexdigest()
    return {
        "kind": "visual_framebuffer_snapshot",
        "frame": frame,
        "screen_source": screen_data["source"],
        "width": screen_data.get("width", 0),
        "height": screen_data.get("height", 0),
        "mode": screen_data.get("mode", ""),
        "byte_count": len(data),
        "sha256": digest,
        "framebuffer": f"sha256:{digest}",
        "sample_size": len(sample),
        "sample_hex": sample.hex().upper(),
        "truncated": len(sample) < len(data),
    }


def read_screen_data(pyboy: Any) -> dict[str, Any]:
    screen = getattr(pyboy, "screen", None)
    if screen is None:
        return {}
    for name in ("ndarray", "image"):
        if not hasattr(screen, name):
            continue
        value = getattr(screen, name)
        if callable(value):
            value = value()
        parsed = screen_data_from_value(value, source=f"screen.{name}")
        if parsed:
            return parsed
    return {}


def screen_data_from_value(value: Any, *, source: str) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, (bytes, bytearray)):
        return {"source": source, "data": bytes(value), "width": 0, "height": 0, "mode": "bytes"}
    if hasattr(value, "tobytes"):
        data = bytes(value.tobytes())
        metadata = screen_metadata(value, source=source)
        metadata["data"] = data
        return metadata
    flattened = flatten_screen_values(value)
    if flattened:
        return {"source": source, "data": bytes(flattened), "width": 0, "height": 0, "mode": "sequence"}
    return {}


def screen_metadata(value: Any, *, source: str) -> dict[str, Any]:
    width = 0
    height = 0
    mode = str(getattr(value, "mode", ""))
    size = getattr(value, "size", None)
    if isinstance(size, tuple) and len(size) >= 2:
        width = int(size[0])
        height = int(size[1])
    shape = getattr(value, "shape", None)
    if isinstance(shape, tuple) and len(shape) >= 2:
        height = int(shape[0])
        width = int(shape[1])
        if len(shape) >= 3 and not mode:
            mode = f"{shape[2]}ch"
    return {"source": source, "width": width, "height": height, "mode": mode}


def flatten_screen_values(value: Any) -> list[int]:
    if not isinstance(value, (list, tuple)):
        return []
    out: list[int] = []
    for item in value:
        if isinstance(item, int):
            out.append(item & 0xFF)
        elif isinstance(item, (list, tuple)):
            out.extend(flatten_screen_values(item))
    return out


def lcd_state(io_registers: dict[str, str]) -> dict[str, Any]:
    lcdc = int(io_registers.get("rLCDC", "00"), 16)
    stat = int(io_registers.get("rSTAT", "00"), 16)
    return {
        "lcd_enabled": bool(lcdc & 0x80),
        "window_tilemap": "9C00" if lcdc & 0x40 else "9800",
        "window_enabled": bool(lcdc & 0x20),
        "bg_window_tile_data": "8000" if lcdc & 0x10 else "8800",
        "bg_tilemap": "9C00" if lcdc & 0x08 else "9800",
        "sprite_size": "8x16" if lcdc & 0x04 else "8x8",
        "sprites_enabled": bool(lcdc & 0x02),
        "bg_enabled": bool(lcdc & 0x01),
        "ppu_mode": stat & 0x03,
        "ly": int(io_registers.get("rLY", "00"), 16),
        "scroll": {
            "scx": int(io_registers.get("rSCX", "00"), 16),
            "scy": int(io_registers.get("rSCY", "00"), 16),
            "wx": int(io_registers.get("rWX", "00"), 16),
            "wy": int(io_registers.get("rWY", "00"), 16),
        },
    }


def visual_snapshot_commands(*, rom_path: str, symbols_path: str, save_state: str, frames: int) -> list[str]:
    base = ["python -m tools.debugger visual-snapshot"]
    if rom_path:
        base.extend(["--rom", quote_arg(rom_path)])
    if symbols_path:
        base.extend(["--symbols", quote_arg(symbols_path)])
    if save_state:
        base.extend(["--save-state", quote_arg(save_state)])
    if frames:
        base.extend(["--frames", str(frames)])
    if save_state:
        commands = [" ".join([*base, "--execute"])]
    else:
        commands = [" ".join([*base, "--save-state", "<state>", "--execute"])]
    trace = ["python -m tools.debugger trace-instructions"]
    if rom_path:
        trace.extend(["--rom", quote_arg(rom_path)])
    if symbols_path:
        trace.extend(["--symbols", quote_arg(symbols_path)])
    if save_state:
        trace.extend(["--save-state", quote_arg(save_state)])
    else:
        trace.extend(["--save-state", "<state>"])
    trace.extend(["--watch-symbol", "wTilemap", "--watch-symbol", "wAttrmap"])
    commands.append(" ".join([*trace, "--execute", "--require-hit"]))
    commands.append("python -m tools.debugger dynamic-taint --report <visual-trace.json> --sink-symbol wTilemap --sink-symbol wAttrmap")
    commands.append("python -m tools.debugger visualize --report <visual-snapshot.json> --format html --out .local\\tmp\\visual_snapshot.html")
    return commands


def quote_arg(value: Any) -> str:
    text = str(value)
    if not text:
        return '""'
    if any(char.isspace() for char in text):
        return '"' + text.replace('"', '\\"') + '"'
    return text
