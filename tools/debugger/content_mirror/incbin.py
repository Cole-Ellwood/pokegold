"""Single INCBIN asset existence + ROM-byte comparison."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from ..provenance import resolve_path
from .helpers import (
    content_invariant,
    evaluate_int_expression,
    first_mismatch,
    format_optional_byte,
    hex_window,
    unique_list,
)


def asset_invariants(parsed: dict[str, Any], *, root: Path, source_file: str) -> list[dict[str, Any]]:
    out = []
    for asset in parsed["assets"]:
        asset_path = str(asset["path"])
        exists = bool(asset["exists"])
        related = [source_file, str(asset.get("display_path") or asset_path)]
        out.append(
            content_invariant(
                invariant_id=f"{source_file}:incbin_asset_exists:{asset_path}",
                invariant_type="incbin_asset_exists",
                status="passed" if exists else "failed",
                severity=78,
                title=(
                    f"INCBIN asset exists: {asset_path}"
                    if exists
                    else f"Missing INCBIN asset: {asset_path}"
                ),
                source_file=source_file,
                line=int(asset["line"]),
                evidence=[f"asset={asset_path}", f"resolved={resolve_path(asset_path, root=root)}"],
                commands=[
                    f"python -m tools.debugger content-mirror --source-file {source_file}",
                    f"python -m tools.debugger gate --changed-file {source_file}",
                    f"python -m tools.debugger provenance --source-file {source_file}",
                ],
                related_files=related,
            )
        )
    return out


def asset_rom_mirror_invariants(
    parsed: dict[str, Any],
    *,
    root: Path,
    source_file: str,
    rom_context: dict[str, Any],
) -> list[dict[str, Any]]:
    if not rom_context.get("available"):
        return []
    out: list[dict[str, Any]] = []
    for asset in parsed["assets"]:
        asset_path = str(asset.get("path", ""))
        rom_label = str(asset.get("rom_label", ""))
        if not asset_path or not rom_label:
            continue
        commands = [
            f"python -m tools.debugger content-mirror --source-file {source_file}",
            f"python -m tools.debugger provenance --source-file {source_file}",
            f"python -m tools.debugger compare --changed-file {source_file}",
        ]
        symbol = rom_context.get("labels", {}).get(rom_label)
        related_files = [source_file, asset_path, str(rom_context.get("rom_path", "")), str(rom_context.get("symbols_path", ""))]
        if not symbol:
            out.append(
                content_invariant(
                    invariant_id=f"{source_file}:incbin_asset_rom_bytes:{asset_path}:{asset.get('line', 0)}",
                    invariant_type="incbin_asset_rom_bytes",
                    status="warning",
                    severity=52,
                    title=f"INCBIN label is missing from built ROM symbols: {rom_label}",
                    source_file=source_file,
                    line=int(asset.get("line", 0)),
                    evidence=[
                        f"asset={asset_path}",
                        f"label={rom_label}",
                        f"symbols={rom_context.get('symbols_path', '')}",
                    ],
                    commands=commands,
                    related_files=related_files,
                    related_symbols=[rom_label],
                )
            )
            continue

        payload = load_incbin_payload(asset, root=root, constants=rom_context.get("constants", {}))
        if payload["errors"]:
            out.append(
                content_invariant(
                    invariant_id=f"{source_file}:incbin_asset_rom_bytes:{asset_path}:{asset.get('line', 0)}",
                    invariant_type="incbin_asset_rom_bytes",
                    status="warning",
                    severity=48,
                    title=f"INCBIN asset could not be encoded for ROM byte comparison: {asset_path}",
                    source_file=source_file,
                    line=int(asset.get("line", 0)),
                    evidence=[
                        f"asset={asset_path}",
                        f"label={rom_label}",
                        *payload["errors"][:8],
                    ],
                    commands=commands,
                    related_files=related_files,
                    related_symbols=[rom_label],
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
            f"asset={asset_path}",
            f"label={rom_label}",
            f"bank=${int(symbol['bank']):02x}",
            f"address=${int(symbol['address']):04x}",
            f"rom_offset=${offset:06x}",
            f"asset_offset={payload['asset_offset']}",
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
                invariant_id=f"{source_file}:incbin_asset_rom_bytes:{asset_path}:{asset.get('line', 0)}",
                invariant_type="incbin_asset_rom_bytes",
                status="passed" if matched else "failed",
                severity=0 if matched else 88,
                title=(
                    f"INCBIN asset ROM bytes match source asset: {asset_path}"
                    if matched
                    else f"INCBIN asset ROM bytes differ from source asset: {asset_path}"
                ),
                source_file=source_file,
                line=int(asset.get("line", 0)),
                evidence=evidence,
                commands=commands,
                related_files=related_files,
                related_symbols=[rom_label],
            )
        )
    return out


def load_incbin_payload(asset: dict[str, Any], *, root: Path, constants: dict[str, int]) -> dict[str, Any]:
    asset_path = str(asset.get("path", ""))
    path = resolve_path(asset_path, root=root)
    errors: list[str] = []
    if not path.exists() or not path.is_file():
        return {"bytes": b"", "asset_offset": 0, "errors": [f"missing_asset={asset_path}"]}
    args = [str(item).strip() for item in asset.get("incbin_args", [])]
    offset = 0
    length: int | None = None
    if len(args) >= 2:
        value = evaluate_int_expression(args[1], constants)
        if value is None:
            errors.append(f"unresolved_asset_offset={args[1]}")
        else:
            offset = value
    if len(args) >= 3:
        value = evaluate_int_expression(args[2], constants)
        if value is None:
            errors.append(f"unresolved_asset_length={args[2]}")
        else:
            length = value
    if len(args) > 3:
        errors.append(f"unsupported_incbin_arg_count={len(args)}")
    data = path.read_bytes()
    if offset < 0 or offset > len(data):
        errors.append(f"asset_offset_out_of_range={offset}")
        offset = max(0, min(offset, len(data)))
    if length is not None and length < 0:
        errors.append(f"asset_length_negative={length}")
        length = 0
    end = len(data) if length is None else min(len(data), offset + length)
    if length is not None and offset + length > len(data):
        errors.append(f"asset_length_out_of_range={length}")
    return {"bytes": data[offset:end], "asset_offset": offset, "errors": unique_list(errors)}
