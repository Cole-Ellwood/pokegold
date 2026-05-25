"""Aggregate INCBIN asset tables (table_width / assert_table_length blocks)."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .helpers import (
    content_invariant,
    first_mismatch,
    format_optional_byte,
    hex_window,
    unique_list,
)
from .incbin import load_incbin_payload


def asset_table_rom_mirror_invariants(
    parsed: dict[str, Any],
    *,
    root: Path,
    source_file: str,
    rom_context: dict[str, Any],
) -> list[dict[str, Any]]:
    if not rom_context.get("available"):
        return []
    out: list[dict[str, Any]] = []
    for table in parsed.get("incbin_tables", []):
        label = str(table.get("label", ""))
        assets = [item for item in table.get("assets", []) if isinstance(item, dict)]
        if not label or len(assets) < 2:
            continue
        commands = [
            f"python -m tools.debugger content-mirror --source-file {source_file}",
            f"python -m tools.debugger provenance --source-file {source_file}",
            f"python -m tools.debugger compare --changed-file {source_file}",
        ]
        related_files = [
            source_file,
            *unique_list(str(asset.get("path", "")) for asset in assets[:12]),
            str(rom_context.get("rom_path", "")),
            str(rom_context.get("symbols_path", "")),
        ]
        if not bool(table.get("eligible", False)):
            continue
        symbol = rom_context.get("labels", {}).get(label)
        if not symbol:
            out.append(
                content_invariant(
                    invariant_id=f"{source_file}:incbin_table_rom_bytes:{label}",
                    invariant_type="incbin_table_rom_bytes",
                    status="warning",
                    severity=50,
                    title=f"INCBIN table label is missing from built ROM symbols: {label}",
                    source_file=source_file,
                    line=int(table.get("line", 0)),
                    evidence=[
                        f"label={label}",
                        f"asset_count={len(assets)}",
                        f"symbols={rom_context.get('symbols_path', '')}",
                    ],
                    commands=commands,
                    related_files=related_files,
                    related_symbols=[label],
                )
            )
            continue
        payload = load_incbin_table_payload(assets, root=root, constants=rom_context.get("constants", {}))
        if payload["errors"]:
            out.append(
                content_invariant(
                    invariant_id=f"{source_file}:incbin_table_rom_bytes:{label}",
                    invariant_type="incbin_table_rom_bytes",
                    status="warning",
                    severity=48,
                    title=f"INCBIN table could not be encoded for ROM byte comparison: {label}",
                    source_file=source_file,
                    line=int(table.get("line", 0)),
                    evidence=[
                        f"label={label}",
                        f"asset_count={len(assets)}",
                        *payload["errors"][:8],
                    ],
                    commands=commands,
                    related_files=related_files,
                    related_symbols=[label],
                )
            )
            continue
        expected = bytes(payload["bytes"])
        rom_bytes = rom_context.get("rom_bytes", b"")
        offset = int(symbol["rom_offset"])
        actual = rom_bytes[offset:offset + len(expected)]
        short_read = len(actual) != len(expected)
        mismatch_index = first_mismatch(expected, actual) if not short_read else min(len(actual), max(0, len(expected) - 1))
        matched = not short_read and mismatch_index < 0
        evidence = [
            f"label={label}",
            f"asset_count={len(assets)}",
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
                invariant_id=f"{source_file}:incbin_table_rom_bytes:{label}",
                invariant_type="incbin_table_rom_bytes",
                status="passed" if matched else "failed",
                severity=0 if matched else 88,
                title=(
                    f"INCBIN table ROM bytes match source assets: {label}"
                    if matched
                    else f"INCBIN table ROM bytes differ from source assets: {label}"
                ),
                source_file=source_file,
                line=int(table.get("line", 0)),
                evidence=evidence,
                commands=commands,
                related_files=related_files,
                related_symbols=[label],
            )
        )
    return out


def load_incbin_table_payload(
    assets: list[dict[str, Any]],
    *,
    root: Path,
    constants: dict[str, int],
) -> dict[str, Any]:
    out = bytearray()
    errors: list[str] = []
    for index, asset in enumerate(assets, start=1):
        payload = load_incbin_payload(asset, root=root, constants=constants)
        for error in payload["errors"]:
            errors.append(f"asset_{index}:{error}")
        out.extend(payload["bytes"])
    return {"bytes": bytes(out), "errors": unique_list(errors)}
