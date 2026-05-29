from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

from .catalog import ROOT
from .provenance import display_path, resolve_path
from .vram_decode import diff_vram_states
from .vram_snapshot import build_vram_snapshot_report, write_json


def build_vram_diff_report(
    *,
    base_state_path: str,
    other_state_path: str,
    root: Path = ROOT,
) -> dict[str, Any]:
    base_state = resolve_path(base_state_path, root=root)
    other_state = resolve_path(other_state_path, root=root)
    base_snapshot = build_vram_snapshot_report(state_path=base_state_path, decode=True, root=root)
    other_snapshot = build_vram_snapshot_report(state_path=other_state_path, decode=True, root=root)
    errors = [
        *(f"base: {item}" for item in base_snapshot.get("errors", [])),
        *(f"other: {item}" for item in other_snapshot.get("errors", [])),
    ]
    warnings = [
        *(f"base: {item}" for item in base_snapshot.get("warnings", [])),
        *(f"other: {item}" for item in other_snapshot.get("warnings", [])),
    ]
    diff: dict[str, Any] = {}
    if not errors:
        diff = diff_vram_states(base_snapshot["decoded"], other_snapshot["decoded"])
    return {
        "schema_version": 1,
        "kind": "unified_debugger_vram_diff",
        "valid": not errors,
        "proof_status": "decoded_snapshot_diff" if not errors else "not_proven",
        "hardware_behavior_proven": False,
        "hardware_proof_boundary": "Structured diff of decoded snapshots; not pixel-accurate PPU rendering proof.",
        "base_state": display_path(base_state, root=root),
        "other_state": display_path(other_state, root=root),
        "base_format": base_snapshot.get("format", {}),
        "other_format": other_snapshot.get("format", {}),
        "diff": diff,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }


def format_vram_diff_report(report: Mapping[str, Any]) -> str:
    diff = report.get("diff", {})
    lines = [
        "VRAM diff",
        f"valid={str(report.get('valid')).lower()} proof={report.get('proof_status', '')}",
        f"base={report.get('base_state', '')}",
        f"other={report.get('other_state', '')}",
    ]
    for warning in report.get("warnings", []):
        lines.append(f"warning: {warning}")
    for error in report.get("errors", []):
        lines.append(f"error: {error}")
    if diff:
        lines.append(
            "changes: "
            f"tilemap_cells={diff.get('tilemap_changed_cell_count', 0)} "
            f"oam={diff.get('oam_changed_count', 0)} "
            f"palettes={diff.get('palette_changed_count', 0)} "
            f"lcdc={diff.get('lcd_changed_count', 0)}"
        )
        for flag in diff.get("scenario_flags", []):
            lines.append(f"flag: {flag.get('id', '')} - {flag.get('reason', '')}")
        for delta in diff.get("tilemap_deltas", [])[:4]:
            lines.append(f"tilemap {delta.get('tilemap', '')}: {delta.get('changed_cell_count', 0)} changed cells")
    return "\n".join(lines)


def self_test() -> str:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "base.bin"
        other = Path(tmp) / "other.bin"
        base_data = bytearray(0x10000)
        other_data = bytearray(0x10000)
        base_data[0x9800] = 0x11
        other_data[0x9800] = 0x22
        base_data[0xFE00 : 0xFE04] = bytes((56, 40, 0x21, 0x00))
        other_data[0xFE00 : 0xFE04] = bytes((56, 40, 0x21, 0x00))
        base_data[0xFF40] = 0x93
        other_data[0xFF40] = 0x93
        base.write_bytes(bytes(base_data))
        other.write_bytes(bytes(other_data))
        report = build_vram_diff_report(base_state_path=str(base), other_state_path=str(other), root=Path(tmp))
    if not report["valid"]:
        raise AssertionError(report["errors"])
    diff = report["diff"]
    if diff["tilemap_changed_cell_count"] != 1:
        raise AssertionError(f"expected 1 tilemap cell delta, got {diff['tilemap_changed_cell_count']}")
    if "tilemap_changed_oam_stable" not in {flag["id"] for flag in diff["scenario_flags"]}:
        raise AssertionError("missing tilemap_changed_oam_stable flag")
    return "vram structured-diff self-test PASS"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.debugger.vram_diff",
        description="Structured VRAM/OAM/tilemap diff for trusted raw 64 KiB snapshots (P6).",
    )
    parser.add_argument("base_state", nargs="?")
    parser.add_argument("other_state", nargs="?")
    parser.add_argument("--json", action="store_true", help="emit structured JSON")
    parser.add_argument("--out", type=Path, default=None, help="write JSON to a file")
    parser.add_argument("--self-test", action="store_true", help="run the P6 structured-diff smoke")
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.self_test:
        print(self_test())
        return 0
    if not args.base_state or not args.other_state:
        parser.error("base_state and other_state are required unless --self-test is used")
    report = build_vram_diff_report(base_state_path=args.base_state, other_state_path=args.other_state)
    if args.out is not None:
        write_json(args.out, report)
        return 0 if report["valid"] else 1
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else format_vram_diff_report(report))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
