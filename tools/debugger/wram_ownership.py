from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .catalog import ROOT
from .provenance import build_provenance_report, display_path, resolve_path


LABEL_RE = re.compile(r"^\s*(?P<label>[A-Za-z_.$][A-Za-z0-9_.$]*)(?:::|:)")


def build_wram_ownership_report(
    *,
    symbols: tuple[str, ...],
    source_file: str = "ram/wram.asm",
    root: Path = ROOT,
) -> dict[str, Any]:
    source = resolve_path(source_file, root=root)
    errors: list[str] = []
    if not symbols:
        errors.append("at least one --symbol is required")
    if not source.exists():
        errors.append(f"missing WRAM source: {source_file}")
    unions = parse_wram_unions(source, root=root) if source.exists() else []
    reports = [
        ownership_for_symbol(symbol, unions=unions, source=source, root=root)
        for symbol in symbols
    ]
    missing = [item["symbol"] for item in reports if item["status"] == "missing"]
    warnings = [f"symbol not found in WRAM unions or labels: {symbol}" for symbol in missing]
    return {
        "schema_version": 1,
        "kind": "unified_debugger_wram_ownership",
        "root": str(root),
        "valid": not errors,
        "source_file": display_path(source, root=root) if source.exists() else source_file,
        "symbols": list(symbols),
        "ownership": reports,
        "union_count": len(unions),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "commands": [
            "python -m tools.debugger localize --symbol " + symbol
            for symbol in symbols
        ],
        "known_limits": [
            "This is a static WRAM layout ownership report. It identifies union co-tenants and source references, not dynamic write order.",
            "Use watch or instruction tracing to prove which co-tenant overwrote a byte in a specific replay.",
        ],
    }


def parse_wram_unions(path: Path, *, root: Path) -> list[dict[str, Any]]:
    unions: list[dict[str, Any]] = []
    stack: list[dict[str, Any]] = []
    all_labels: list[dict[str, Any]] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        code = raw.split(";", 1)[0].strip()
        if code == "UNION":
            union = {
                "source_file": display_path(path, root=root),
                "start_line": line_no,
                "end_line": 0,
                "arms": [{"index": 0, "start_line": line_no + 1, "labels": []}],
            }
            stack.append(union)
            continue
        if code == "NEXTU" and stack:
            active = stack[-1]
            active["arms"].append({"index": len(active["arms"]), "start_line": line_no + 1, "labels": []})
            continue
        if code == "ENDU" and stack:
            active = stack.pop()
            active["end_line"] = line_no
            unions.append(active)
            continue
        match = LABEL_RE.match(raw)
        if not match:
            continue
        label = {"name": match.group("label"), "line": line_no}
        all_labels.append(label)
        if stack:
            stack[-1]["arms"][-1]["labels"].append(label)
    for label in all_labels:
        if not any(label in arm["labels"] for union in unions for arm in union["arms"]):
            unions.append(
                {
                    "source_file": display_path(path, root=root),
                    "start_line": label["line"],
                    "end_line": label["line"],
                    "fixed_label": True,
                    "arms": [{"index": 0, "start_line": label["line"], "labels": [label]}],
                }
            )
    return unions


def ownership_for_symbol(
    symbol: str,
    *,
    unions: list[dict[str, Any]],
    source: Path,
    root: Path,
) -> dict[str, Any]:
    for union in unions:
        for arm in union["arms"]:
            names = [label["name"] for label in arm["labels"]]
            if symbol not in names:
                continue
            other_arms = [
                {
                    "index": other["index"],
                    "start_line": other["start_line"],
                    "labels": [label["name"] for label in other["labels"]],
                }
                for other in union["arms"]
                if other is not arm
            ]
            provenance = build_provenance_report(
                symbols_path=str(root / "pokegold.sym"),
                symbols=(symbol,),
                max_hits=12,
                root=root,
            ) if (root / "pokegold.sym").exists() else None
            return {
                "symbol": symbol,
                "status": "fixed" if union.get("fixed_label") else "union_member",
                "source_file": display_path(source, root=root),
                "line": next(label["line"] for label in arm["labels"] if label["name"] == symbol),
                "union_start_line": union["start_line"],
                "union_end_line": union["end_line"],
                "arm_index": arm["index"],
                "same_arm_labels": names,
                "other_union_arms": other_arms,
                "other_union_arm_count": len(other_arms),
                "risk": (
                    "high" if other_arms else "low"
                ),
                "provenance": provenance,
            }
    return {
        "symbol": symbol,
        "status": "missing",
        "source_file": display_path(source, root=root),
        "risk": "unknown",
    }
