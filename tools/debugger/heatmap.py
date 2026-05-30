#!/usr/bin/env python3
"""IO heatmap + per-frame memory-write timeline (P9).

`debugger heatmap --trace X --region io|wramx|hram [--frame-range A:B]`
produces a per-frame ASCII grid of write density across the chosen
memory region plus a structured JSON payload carrying the per-cell
last-write PC for hover/click reveal.

First slice scope is the read-only emit surface: write-count grid +
JSON. Selftest growth, taint integration, and the
`test_heatmap_last_write_pc_matches_when_wrote_query` cross-check land
in P9 follow-up slices.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .catalog import ROOT


SCHEMA_VERSION = 1
DEFAULT_FRAME_BUCKETS = 24

REGIONS: dict[str, tuple[int, int]] = {
    "io": (0xFF00, 0xFF80),
    "hram": (0xFF80, 0xFFFF),
    "wramx": (0xD000, 0xE000),
}

DENSITY_GLYPHS = " ._:!*#"


def _parse_address(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value & 0xFFFF
    text = str(value).strip()
    if not text:
        return None
    if ":" in text:
        _, _, tail = text.rpartition(":")
        text = tail
    text = text.removeprefix("0x").removeprefix("$").removeprefix("#")
    try:
        return int(text, 16) & 0xFFFF
    except ValueError:
        return None


def _parse_frame(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_frame_range(spec: str | None) -> tuple[int, int] | None:
    if not spec:
        return None
    text = spec.strip()
    if ":" not in text:
        return None
    lo_text, _, hi_text = text.partition(":")
    try:
        lo = int(lo_text) if lo_text else 0
        hi = int(hi_text) if hi_text else (1 << 31)
    except ValueError:
        return None
    if hi <= lo:
        return None
    return lo, hi


def _first_present(ev: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in ev and ev[key] is not None:
            return ev[key]
    return None


def _load_trace_events(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return ()
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        return ()
    lines = [line for line in (raw.strip() for raw in text.splitlines()) if line]
    if len(lines) == 1:
        try:
            payload = json.loads(lines[0])
        except json.JSONDecodeError:
            return ()
        if isinstance(payload, dict):
            candidate = payload.get("events")
            if isinstance(candidate, list):
                return candidate
            return [payload]
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        return ()
    events: list[dict[str, Any]] = []
    for line in lines:
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(ev, dict):
            events.append(ev)
    return events


def build_heatmap(
    *,
    traces: Sequence[str | Path],
    region: str = "io",
    frame_range: tuple[int, int] | None = None,
    frame_buckets: int = DEFAULT_FRAME_BUCKETS,
    root: Path = ROOT,
) -> dict[str, Any]:
    region_key = region.lower().strip()
    if region_key not in REGIONS:
        return {
            "kind": "unified_debugger_io_heatmap",
            "schema_version": SCHEMA_VERSION,
            "valid": False,
            "region": region_key,
            "errors": [f"unknown region {region!r}; expected one of {sorted(REGIONS)}"],
            "grid": "",
            "cells": [],
        }
    lo, hi = REGIONS[region_key]
    addr_count = hi - lo

    cells_by_key: dict[tuple[int, int], dict[str, Any]] = {}
    frames_seen: set[int] = set()
    errors: list[str] = []

    for trace in traces:
        trace_path = Path(trace) if Path(trace).is_absolute() else root / trace
        if not trace_path.exists():
            errors.append(f"missing trace: {trace}")
            continue
        for ev in _load_trace_events(trace_path):
            if not isinstance(ev, dict):
                continue
            if ev.get("kind") not in (None, "write", "memory_write"):
                continue
            addr = _parse_address(_first_present(ev, "address", "addr", "bank_address"))
            if addr is None or addr < lo or addr >= hi:
                continue
            frame = _parse_frame(_first_present(ev, "frame", "frame_index"))
            if frame is None:
                frame = 0
            if frame_range is not None:
                f_lo, f_hi = frame_range
                if frame < f_lo or frame >= f_hi:
                    continue
            key = (frame, addr)
            cell = cells_by_key.setdefault(
                key,
                {
                    "frame": frame,
                    "address": addr,
                    "address_hex": f"${addr:04X}",
                    "write_count": 0,
                    "last_write_pc": "",
                    "last_write_pc_label": "",
                    "last_write_seq": -1,
                },
            )
            cell["write_count"] += 1
            seq = ev.get("seq")
            seq_value = _parse_frame(seq) if seq is not None else None
            if seq_value is not None and seq_value > cell["last_write_seq"]:
                pc = ev.get("pc_bank_address") or ev.get("pc") or ""
                pc_label = ev.get("pc_label") or ""
                cell["last_write_pc"] = str(pc)
                cell["last_write_pc_label"] = str(pc_label)
                cell["last_write_seq"] = seq_value
            elif seq_value is None and not cell["last_write_pc"]:
                pc = ev.get("pc_bank_address") or ev.get("pc") or ""
                pc_label = ev.get("pc_label") or ""
                cell["last_write_pc"] = str(pc)
                cell["last_write_pc_label"] = str(pc_label)
            frames_seen.add(frame)

    cells = sorted(cells_by_key.values(), key=lambda c: (c["frame"], c["address"]))
    sorted_frames = sorted(frames_seen)
    grid_lines = _render_grid(cells, frames=sorted_frames, region=region_key, lo=lo, hi=hi)

    return {
        "kind": "unified_debugger_io_heatmap",
        "schema_version": SCHEMA_VERSION,
        "valid": not errors,
        "region": region_key,
        "region_start_hex": f"${lo:04X}",
        "region_end_hex": f"${hi - 1:04X}",
        "address_count": addr_count,
        "frame_count": len(sorted_frames),
        "frames": sorted_frames,
        "frame_range_filter": (
            {"lo": frame_range[0], "hi": frame_range[1]} if frame_range else None
        ),
        "cell_count": len(cells),
        "cells": cells,
        "errors": errors,
        "grid": "\n".join(grid_lines),
    }


def _render_grid(
    cells: Sequence[dict[str, Any]],
    *,
    frames: Sequence[int],
    region: str,
    lo: int,
    hi: int,
) -> list[str]:
    if not cells or not frames:
        return [
            f"# {region} heatmap (${lo:04X}-${hi - 1:04X})",
            "(no writes in window)",
        ]
    addresses = sorted({cell["address"] for cell in cells})
    by_key = {(cell["frame"], cell["address"]): cell for cell in cells}
    max_count = max(cell["write_count"] for cell in cells) or 1
    glyph_max = len(DENSITY_GLYPHS) - 1
    lines: list[str] = [
        f"# {region} heatmap (${lo:04X}-${hi - 1:04X})",
        f"# frames {frames[0]}..{frames[-1]} columns; addresses {len(addresses)} rows",
    ]
    header = "        " + "".join(f"{f % 10}" for f in frames)
    lines.append(header)
    for addr in addresses:
        row_cells = []
        for frame in frames:
            cell = by_key.get((frame, addr))
            if cell is None:
                row_cells.append(DENSITY_GLYPHS[0])
                continue
            scaled = round(cell["write_count"] / max_count * glyph_max)
            scaled = max(1, min(glyph_max, scaled))
            row_cells.append(DENSITY_GLYPHS[scaled])
        lines.append(f"${addr:04X}  {''.join(row_cells)}")
    return lines


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.debugger.heatmap",
        description=(
            "Per-frame memory-write heatmap for IO/HRAM/WRAMX regions (P9). "
            "Emits ASCII grid by default plus structured JSON with per-cell "
            "last-write PC. Ships write-count buckets; richer predicates "
            "(read counts, taint overlay, --explain) are a future addition."
        ),
    )
    parser.add_argument(
        "--trace",
        action="append",
        default=[],
        help="trace JSONL or JSON path (repeatable)",
    )
    parser.add_argument(
        "--region",
        choices=sorted(REGIONS),
        default="io",
        help="memory region (default: io)",
    )
    parser.add_argument(
        "--frame-range",
        type=str,
        default=None,
        help="A:B inclusive-lower exclusive-upper frame window",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit JSON instead of the ASCII grid",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="write JSON to a file (implies --json)",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    frame_range = _parse_frame_range(args.frame_range)
    if args.frame_range and frame_range is None:
        parser.error("--frame-range must be A:B with hi greater than lo")

    report = build_heatmap(
        traces=tuple(args.trace),
        region=args.region,
        frame_range=frame_range,
    )

    if args.out is not None:
        args.out.write_text(json.dumps(report, sort_keys=True), encoding="utf-8")
        return 0 if report.get("valid") else 1
    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        sys.stdout.write(report["grid"])
        sys.stdout.write("\n")
    return 0 if report.get("valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())
