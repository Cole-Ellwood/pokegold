from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .catalog import ROOT
from .provenance import display_path, parse_symbol_table, resolve_path
from .wram_ownership import build_wram_ownership_report


DEFAULT_BARRIER_SYMBOL = "Script_startbattle"
DEFAULT_SOURCE_FILE = "engine/overworld/scripting.asm"


def build_wram_lifetime_report(
    *,
    symbols: tuple[str, ...],
    through: str = DEFAULT_BARRIER_SYMBOL,
    source_file: str = DEFAULT_SOURCE_FILE,
    symbols_path: str = "pokegold.sym",
    root: Path = ROOT,
) -> dict[str, Any]:
    errors: list[str] = []
    if not symbols:
        errors.append("at least one --symbol is required")
    source = resolve_path(source_file, root=root)
    if not source.exists():
        errors.append(f"missing source file: {source_file}")
    sym_path = resolve_path(symbols_path, root=root)
    if not sym_path.exists():
        errors.append(f"missing symbols: {symbols_path}")

    symbol_table = parse_symbol_table(sym_path) if sym_path.exists() else {}
    ownership = (
        build_wram_ownership_report(symbols=symbols, root=root)
        if symbols and not errors
        else {}
    )
    routine = extract_routine(source, through) if source.exists() else {}
    findings = build_lifetime_findings(
        symbols=symbols,
        ownership=ownership,
        routine=routine,
        symbol_table=symbol_table,
    )
    failed = [finding for finding in findings if int(finding.get("severity", 3)) <= 2]
    commands = [
        "python -m tools.debugger wram-ownership " + " ".join(f"--symbol {symbol}" for symbol in symbols),
        f"python -m tools.debugger provenance {' '.join(f'--symbol {symbol}' for symbol in symbols)}",
        "python -m tools.debugger state-inspect --save-state <crash-state.sgm> --rom pokegold.gbc --symbols pokegold.sym",
    ]
    return {
        "schema_version": 1,
        "kind": "unified_debugger_wram_lifetime_report",
        "root": str(root),
        "valid": not errors,
        "passed": not errors and not failed,
        "symbols": list(symbols),
        "through": through,
        "source_file": display_path(source, root=root) if source.exists() else source_file,
        "routine": routine,
        "ownership": ownership,
        "finding_count": len(findings),
        "findings": findings,
        "error_count": len(errors),
        "warning_count": 0,
        "errors": errors,
        "warnings": [],
        "commands": commands,
        "known_limits": [
            "This is a static lifetime/barrier report. It proves whether a known volatile range is protected in source, not dynamic write order.",
            "Use state-inspect or watch to prove a specific captured state or replay.",
        ],
    }


def build_lifetime_findings(
    *,
    symbols: tuple[str, ...],
    ownership: dict[str, Any],
    routine: dict[str, Any],
    symbol_table: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    if not symbols:
        return []
    union_items = [
        item
        for item in ownership.get("ownership", [])
        if item.get("status") == "union_member"
    ]
    if not union_items:
        return []
    protected = bool(routine.get("trainer_context_protected"))
    severity = 3 if protected else 1
    first = union_items[0]
    overlap_labels: list[str] = []
    for arm in first.get("other_union_arms", []):
        overlap_labels.extend(str(label) for label in arm.get("labels", []))
    range_start = symbol_table.get("wSeenTrainerBank") or symbol_table.get(symbols[0])
    range_end = symbol_table.get("wTempTrainerEnd")
    address_range = ""
    if range_start and range_end:
        end_address = int(range_end["address"]) - 1
        address_range = f"{range_start['bank_hex']}:{range_start['address_hex']}..{int(range_start['bank']):02X}:{end_address:04X}"
    status = "protected" if protected else "unprotected"
    title = (
        "Volatile WRAM union state is protected across StartBattle/evolution barrier"
        if protected
        else "Volatile WRAM union state crosses StartBattle/evolution barrier without backup"
    )
    return [
        {
            "id": f"volatile_trainer_union_{status}",
            "severity": severity,
            "title": title,
            "range": "wSeenTrainerBank..wTempTrainerEnd",
            "address_range": address_range,
            "volatile_reason": "union_overlap",
            "overlap_labels": overlap_labels[:20],
            "barriers": [routine.get("barrier", "Script_startbattle -> predef StartBattle")],
            "post_barrier_reads": ["Script_scripttalkafter", "Script_endifjustbattled"],
            "protection": routine.get("protection", {}),
            "suggested_watch": list(symbols),
        }
    ]


def extract_routine(path: Path, label: str) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    start = None
    for index, line in enumerate(lines):
        if re.match(rf"^{re.escape(label)}:\s*$", line):
            start = index
            break
    if start is None:
        return {
            "found": False,
            "label": label,
            "errors": [f"routine label not found: {label}"],
        }
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*:\s*$", lines[index]):
            end = index
            break
    body = lines[start:end]
    barrier_indexes = [idx for idx, line in enumerate(body) if "predef StartBattle" in line]
    backup_indexes = [idx for idx, line in enumerate(body) if "wTrainerBattleContextBackup" in line]
    active_indexes = [idx for idx, line in enumerate(body) if "wTrainerBattleContextBackupActive" in line]
    save_call_before = any(
        "SaveTrainerContext" in line
        for idx, line in enumerate(body)
        if not barrier_indexes or idx < barrier_indexes[0]
    )
    restore_call_after = any(
        "RestoreTrainerContext" in line
        for idx, line in enumerate(body)
        if barrier_indexes and idx > barrier_indexes[0]
    )
    protected = bool(barrier_indexes and backup_indexes and active_indexes and save_call_before and restore_call_after)
    return {
        "found": True,
        "label": label,
        "start_line": start + 1,
        "end_line": end,
        "barrier": f"{label} -> predef StartBattle",
        "trainer_context_protected": protected,
        "protection": {
            "save_call_before_barrier": save_call_before,
            "restore_call_after_barrier": restore_call_after,
            "backup_symbol_references": len(backup_indexes),
            "active_flag_references": len(active_indexes),
        },
        "source_excerpt": [
            {"line": start + idx + 1, "text": line.strip()}
            for idx, line in enumerate(body)
            if "StartBattle" in line or "TrainerContext" in line or "wTrainerBattleContextBackup" in line
        ],
    }
