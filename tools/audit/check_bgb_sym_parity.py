#!/usr/bin/env python3
"""Audit that BGB/Emulicious symbols preserve the RGBDS symbol set."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from emit_bgb_sym import Symbol, parse_symbol_file  # noqa: E402


def _symbol_index(symbols: list[Symbol]) -> dict[str, tuple[int, int]]:
    out: dict[str, tuple[int, int]] = {}
    for symbol in symbols:
        out.setdefault(symbol.label, (symbol.bank, symbol.address))
    return out


def build_parity_report(*, symbols_path: Path, bgb_symbols_path: Path) -> dict[str, object]:
    errors: list[str] = []
    missing: list[str] = []
    mismatched: list[dict[str, object]] = []
    if not symbols_path.exists():
        errors.append(f"missing source symbol file: {symbols_path}")
        source_symbols: list[Symbol] = []
    else:
        source_symbols = parse_symbol_file(symbols_path)
    if not bgb_symbols_path.exists():
        errors.append(f"missing BGB symbol file: {bgb_symbols_path}")
        bgb_symbols: list[Symbol] = []
    else:
        bgb_symbols = parse_symbol_file(bgb_symbols_path)

    source_index = _symbol_index(source_symbols)
    bgb_index = _symbol_index(bgb_symbols)
    for label, source_addr in sorted(source_index.items()):
        bgb_addr = bgb_index.get(label)
        if bgb_addr is None:
            missing.append(label)
            continue
        if bgb_addr != source_addr:
            mismatched.append(
                {
                    "label": label,
                    "expected": f"{source_addr[0]:02X}:{source_addr[1]:04X}",
                    "observed": f"{bgb_addr[0]:02X}:{bgb_addr[1]:04X}",
                }
            )
    ok = not errors and not missing and not mismatched
    return {
        "ok": ok,
        "symbols": str(symbols_path),
        "bgb_symbols": str(bgb_symbols_path),
        "source_symbol_count": len(source_index),
        "bgb_symbol_count": len(bgb_index),
        "missing_count": len(missing),
        "mismatch_count": len(mismatched),
        "errors": errors,
        "missing_symbols": missing[:50],
        "mismatched_symbols": mismatched[:50],
    }


def format_report(report: dict[str, object]) -> str:
    lines = ["BGB symbol parity audit"]
    lines.append(f"source: {report['symbols']}")
    lines.append(f"bgb: {report['bgb_symbols']}")
    if report["ok"]:
        lines.append(
            f"PASS: {report['source_symbol_count']} source symbols preserved in BGB export"
        )
        return "\n".join(lines)
    lines.append(
        "FAIL: "
        f"{report['missing_count']} missing, {report['mismatch_count']} address mismatch, "
        f"{len(report['errors'])} file error(s)"
    )
    for error in report["errors"]:
        lines.append(f"  {error}")
    for label in report["missing_symbols"]:
        lines.append(f"  missing: {label}")
    for mismatch in report["mismatched_symbols"]:
        lines.append(
            f"  mismatch: {mismatch['label']} expected {mismatch['expected']} observed {mismatch['observed']}"
        )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fail if a BGB/Emulicious .sym export is missing RGBDS symbols."
    )
    parser.add_argument("--symbols", default="pokegold.sym", help="source RGBDS .sym path")
    parser.add_argument("--bgb-symbols", default="pokegold.bgb.sym", help="BGB-compatible .sym path")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(list(argv) if argv is not None else None)

    symbols_path = (ROOT / args.symbols).resolve() if not Path(args.symbols).is_absolute() else Path(args.symbols)
    bgb_symbols_path = (
        (ROOT / args.bgb_symbols).resolve()
        if not Path(args.bgb_symbols).is_absolute()
        else Path(args.bgb_symbols)
    )
    report = build_parity_report(symbols_path=symbols_path, bgb_symbols_path=bgb_symbols_path)
    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        print(format_report(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
