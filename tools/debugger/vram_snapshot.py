from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

from .catalog import ROOT
from .ingest import sha256_file
from .provenance import display_path, resolve_path
from .save_state_lab import address_to_offset, classify_save_state_bytes
from .vram_decode import IO_REGISTER_NAMES, OAM_SIZE, VRAM_SIZE, decode_vram_state


VRAM_START = 0x8000
OAM_START = 0xFE00
P6_RAW_MEMORY_LIMIT = "V0 decodes trusted raw 64 KiB address-space images only; opaque emulator state formats fail closed."


def build_vram_snapshot_report(
    *,
    state_path: str,
    decode: bool = False,
    root: Path = ROOT,
) -> dict[str, Any]:
    state = resolve_path(state_path, root=root)
    errors: list[str] = []
    warnings: list[str] = []
    data = b""
    if not state.exists():
        errors.append(f"missing state file: {state_path}")
    else:
        data = state.read_bytes()
    classification = classify_save_state_bytes(data, suffix=state.suffix if state.exists() else "")
    warnings.extend(classification.get("warnings", []))
    report: dict[str, Any] = {
        "schema_version": 1,
        "kind": "unified_debugger_vram_snapshot",
        "valid": False,
        "proof_status": "planned_only",
        "hardware_behavior_proven": False,
        "hardware_proof_boundary": "Decoded snapshot bytes are not pixel-accurate PPU rendering proof.",
        "state": display_path(state, root=root),
        "state_sha256": sha256_file(state) if state.exists() else "",
        "format": classification,
        "decode_requested": decode,
        "decoded": {},
        "error_count": 0,
        "warning_count": 0,
        "errors": errors,
        "warnings": warnings,
        "known_limits": [
            P6_RAW_MEMORY_LIMIT,
            "Raw 64 KiB images expose one CPU-visible VRAM aperture; CGB VRAM bank 1 attributes require a paired bank capture.",
        ],
    }
    if errors:
        return finalize_report(report)
    if not decode:
        warnings.append("decode not requested; pass --decode to structure VRAM/OAM surfaces")
        report["valid"] = True
        return finalize_report(report)
    if classification.get("address_map") != "full_16bit":
        errors.append(f"unsupported state format for vram decode: {classification.get('id', 'unknown')}")
        return finalize_report(report)

    try:
        vram = read_address_range(data, classification, VRAM_START, VRAM_SIZE)
        oam = read_address_range(data, classification, OAM_START, OAM_SIZE)
        io_registers = read_io_registers(data, classification)
    except ValueError as exc:
        errors.append(str(exc))
        return finalize_report(report)

    if int(io_registers.get("rVBK", "00"), 16) & 0x01:
        warnings.append(
            "raw memory has rVBK bit0 set; $8000-$9FFF may reflect active VRAM bank 1, "
            "but V0 cannot pair it with bank 0"
        )
    decoded = decode_vram_state(vram, oam=oam, io_registers=io_registers)
    report["valid"] = True
    report["proof_status"] = decoded["proof_status"]
    report["decoded"] = decoded
    return finalize_report(report)


def read_address_range(data: bytes, classification: Mapping[str, Any], start: int, size: int) -> bytes:
    out = bytearray()
    for offset in range(size):
        address = start + offset
        state_offset = address_to_offset(dict(classification), address)
        if state_offset is None or state_offset >= len(data):
            raise ValueError(f"state format does not map required address ${address:04X}")
        out.append(data[state_offset])
    return bytes(out)


def read_io_registers(data: bytes, classification: Mapping[str, Any]) -> dict[str, str]:
    registers: dict[str, str] = {}
    for address, name in IO_REGISTER_NAMES.items():
        state_offset = address_to_offset(dict(classification), address)
        if state_offset is None or state_offset >= len(data):
            continue
        registers[name] = f"{data[state_offset] & 0xFF:02X}"
    return registers


def finalize_report(report: dict[str, Any]) -> dict[str, Any]:
    report["error_count"] = len(report["errors"])
    report["warning_count"] = len(report["warnings"])
    if report["errors"]:
        report["valid"] = False
    return report


def format_vram_snapshot_report(report: Mapping[str, Any]) -> str:
    fmt = report.get("format", {})
    decoded = report.get("decoded", {})
    lines = [
        "VRAM snapshot",
        f"valid={str(report.get('valid')).lower()} format={fmt.get('id', '')} proof={report.get('proof_status', '')}",
        f"state={report.get('state', '')}",
    ]
    for warning in report.get("warnings", []):
        lines.append(f"warning: {warning}")
    for error in report.get("errors", []):
        lines.append(f"error: {error}")
    if decoded:
        tilemaps = decoded.get("tilemaps", {})
        oam = decoded.get("oam", {})
        lcd = decoded.get("lcd_state", {})
        lines.append(
            "decoded: "
            f"bg={lcd.get('bg_tilemap', '')} window={lcd.get('window_tilemap', '')} "
            f"oam_visible_guess={oam.get('visible_guess_count', 0)} "
            f"tilemaps={','.join(tilemaps.keys())}"
        )
    return "\n".join(lines)


def write_json(path: Path, report: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")


def self_test() -> str:
    with tempfile.TemporaryDirectory() as tmp:
        state = Path(tmp) / "raw.bin"
        data = bytearray(0x10000)
        data[0x9800] = 0x2A
        data[0xFE00 : 0xFE04] = bytes((56, 40, 0x21, 0x10))
        data[0xFF40] = 0x93
        data[0xFF47] = 0xE4
        state.write_bytes(bytes(data))
        report = build_vram_snapshot_report(state_path=str(state), decode=True, root=Path(tmp))
    if not report["valid"]:
        raise AssertionError(report["errors"])
    decoded = report["decoded"]
    if decoded["tilemaps"]["9800"]["cells"][0]["tile_hex"] != "2A":
        raise AssertionError("tilemap decode did not preserve tile 2A at $9800")
    if decoded["oam"]["visible_guess_count"] != 1:
        raise AssertionError("OAM visible sprite smoke failed")
    return "vram structured-decode self-test PASS"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.debugger.vram_snapshot",
        description="Decode VRAM/OAM/tilemap state from trusted raw 64 KiB snapshots (P6).",
    )
    parser.add_argument("--save-state", default="", help="raw 64 KiB state image to decode")
    parser.add_argument("--decode", action="store_true", help="decode VRAM/OAM/LCDC/palette structures")
    parser.add_argument("--json", action="store_true", help="emit structured JSON")
    parser.add_argument("--out", type=Path, default=None, help="write JSON to a file")
    parser.add_argument("--self-test", action="store_true", help="run the P6 structured-decode smoke")
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.self_test:
        print(self_test())
        return 0
    if not args.save_state:
        parser.error("--save-state is required unless --self-test is used")
    report = build_vram_snapshot_report(state_path=args.save_state, decode=args.decode)
    if args.out is not None:
        write_json(args.out, report)
        return 0 if report["valid"] else 1
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else format_vram_snapshot_report(report))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
