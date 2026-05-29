from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from .catalog import ROOT
from .ingest import sha256_file
from .minimize import unique_list
from .provenance import display_path, parse_symbol_table, resolve_path


RAW_MEMORY_SIZE = 0x10000
RAW_WRAM_SIZE = 0x2000
WRAM_START = 0xC000
WRAM_END = 0xDFFF

DEFAULT_SYMBOLS = (
    "wMapGroup",
    "wMapNumber",
    "wXCoord",
    "wYCoord",
    "wBattleMode",
    "hBattleTurn",
    "wCurDamage",
    "wBattleMonHP",
    "wEnemyMonHP",
    "wPartyCount",
    "wScriptRunning",
    "wScriptMode",
    "wScriptPos",
    "wEventFlags",
    "hROMBank",
)

SYMBOL_SIZES = {
    "wCurDamage": 2,
    "wBattleMonHP": 2,
    "wEnemyMonHP": 2,
    "wScriptPos": 2,
}


def build_save_state_inspect_report(
    *,
    state_path: str,
    symbols_path: str = "pokegold.sym",
    symbols: tuple[str, ...] = (),
    max_symbols: int = 32,
    root: Path = ROOT,
) -> dict[str, Any]:
    state = resolve_path(state_path, root=root)
    sym = resolve_path(symbols_path, root=root)
    errors: list[str] = []
    warnings: list[str] = []
    symbol_table: dict[str, dict[str, Any]] = {}

    if not state.exists():
        errors.append(f"missing state file: {state_path}")
        data = b""
    else:
        data = state.read_bytes()

    if sym.exists():
        symbol_table = parse_symbol_table(sym)
    else:
        warnings.append(f"missing symbols: {symbols_path}")

    classification = classify_save_state_bytes(data, suffix=state.suffix)
    warnings.extend(classification["warnings"])
    requested_symbols = selected_symbols(symbols, symbol_table=symbol_table, max_symbols=max_symbols)
    symbol_values = read_symbol_values(
        data,
        classification=classification,
        symbol_table=symbol_table,
        symbols=tuple(requested_symbols),
    )

    return {
        "schema_version": 1,
        "kind": "unified_debugger_save_state_inspect",
        "root": str(root),
        "valid": not errors,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "state": display_path(state, root=root),
        "symbols_path": display_path(sym, root=root),
        "symbols_sha256": sha256_file(sym) if sym.exists() else "",
        "file": file_metadata(state, data=data) if state.exists() else {},
        "format": classification,
        "symbol_count": len(symbol_values),
        "symbols": symbol_values,
        "known_limits": [
            "V0 decodes only formats with an explicit address map.",
            "VBA/VBA-M .sgm files are identified but not trusted for WRAM decoding until a format proof lands.",
            "Raw WRAM images expose address-slot bytes; they do not prove the active WRAMX bank.",
        ],
    }


def build_save_state_diff_report(
    *,
    base_state_path: str,
    other_state_path: str,
    symbols_path: str = "pokegold.sym",
    symbols: tuple[str, ...] = (),
    max_deltas: int = 64,
    root: Path = ROOT,
) -> dict[str, Any]:
    base = resolve_path(base_state_path, root=root)
    other = resolve_path(other_state_path, root=root)
    sym = resolve_path(symbols_path, root=root)
    errors: list[str] = []
    warnings: list[str] = []
    symbol_table: dict[str, dict[str, Any]] = {}

    if not base.exists():
        errors.append(f"missing base state file: {base_state_path}")
        base_data = b""
    else:
        base_data = base.read_bytes()
    if not other.exists():
        errors.append(f"missing other state file: {other_state_path}")
        other_data = b""
    else:
        other_data = other.read_bytes()

    if sym.exists():
        symbol_table = parse_symbol_table(sym)
    else:
        warnings.append(f"missing symbols: {symbols_path}")

    base_format = classify_save_state_bytes(base_data, suffix=base.suffix)
    other_format = classify_save_state_bytes(other_data, suffix=other.suffix)
    warnings.extend([f"base: {item}" for item in base_format["warnings"]])
    warnings.extend([f"other: {item}" for item in other_format["warnings"]])

    common_addresses = sorted(set(address_iter(base_format)) & set(address_iter(other_format)))
    deltas: list[dict[str, Any]] = []
    for address in common_addresses:
        base_offset = address_to_offset(base_format, address)
        other_offset = address_to_offset(other_format, address)
        if base_offset is None or other_offset is None:
            continue
        before = base_data[base_offset]
        after = other_data[other_offset]
        if before == after:
            continue
        if len(deltas) < max_deltas:
            deltas.append(
                {
                    "address": f"{address:04X}",
                    "base_offset": base_offset,
                    "other_offset": other_offset,
                    "before": before,
                    "before_hex": f"{before:02X}",
                    "after": after,
                    "after_hex": f"{after:02X}",
                }
            )

    if not errors and not common_addresses:
        errors.append(
            "cannot diff these state formats without a trusted address map: "
            f"{base_format['id']} vs {other_format['id']}"
        )

    requested_symbols = selected_symbols(symbols, symbol_table=symbol_table, max_symbols=256)
    symbol_deltas = symbol_delta_records(
        base_data,
        other_data,
        base_format=base_format,
        other_format=other_format,
        symbol_table=symbol_table,
        symbols=tuple(requested_symbols),
    )

    return {
        "schema_version": 1,
        "kind": "unified_debugger_save_state_diff",
        "root": str(root),
        "valid": not errors,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "base_state": display_path(base, root=root),
        "other_state": display_path(other, root=root),
        "symbols_path": display_path(sym, root=root),
        "symbols_sha256": sha256_file(sym) if sym.exists() else "",
        "base_format": base_format,
        "other_format": other_format,
        "address_space": address_space_summary(common_addresses),
        "changed_byte_count": count_changed_bytes(base_data, other_data, base_format=base_format, other_format=other_format),
        "sample_delta_count": len(deltas),
        "sample_deltas": deltas,
        "symbol_delta_count": len(symbol_deltas),
        "symbol_deltas": symbol_deltas,
        "known_limits": [
            "Address diffs compare decoded address-map bytes, not full emulator internals.",
            "Unsupported state formats fail closed instead of guessing WRAM offsets.",
        ],
    }


def classify_save_state_bytes(data: bytes, *, suffix: str = "") -> dict[str, Any]:
    suffix_lower = suffix.lower()
    size = len(data)
    warnings: list[str] = []
    header = data[:32]
    ascii_header = printable_ascii(header)

    if size == RAW_MEMORY_SIZE:
        return {
            "id": "raw_memory_64k",
            "title": "Raw 64 KiB address-space image",
            "confidence": "high",
            "decode_supported": True,
            "address_map": "full_16bit",
            "mapped_address_start": "0000",
            "mapped_address_end": "FFFF",
            "size": size,
            "header_ascii": ascii_header,
            "warnings": warnings,
        }
    if size == RAW_WRAM_SIZE:
        return {
            "id": "raw_wram_8k",
            "title": "Raw 8 KiB WRAM address-slot image",
            "confidence": "medium",
            "decode_supported": True,
            "address_map": "wram_c000_dfff",
            "mapped_address_start": f"{WRAM_START:04X}",
            "mapped_address_end": f"{WRAM_END:04X}",
            "size": size,
            "header_ascii": ascii_header,
            "warnings": [
                "raw WRAM does not identify which WRAMX bank was active for D000-DFFF addresses",
            ],
        }

    sgm_candidate = suffix_lower == ".sgm" or looks_like_vba_sgm(data)
    if sgm_candidate:
        title = vba_title(data)
        version = int.from_bytes(data[:4], "little") if len(data) >= 4 else None
        warnings.append("recognized VBA/VBA-M .sgm candidate, but V0 has no trusted WRAM offset decoder")
        return {
            "id": "vba_sgm_candidate",
            "title": "VBA/VBA-M .sgm candidate",
            "confidence": "medium" if title else "low",
            "decode_supported": False,
            "address_map": "",
            "size": size,
            "vba_version_le": version,
            "rom_title": title,
            "header_ascii": ascii_header,
            "warnings": warnings,
        }

    if suffix_lower == ".state":
        warnings.append("PyBoy state candidate requires emulator loading before WRAM bytes can be trusted")
        return {
            "id": "pyboy_state_candidate",
            "title": "PyBoy state candidate",
            "confidence": "low",
            "decode_supported": False,
            "address_map": "",
            "size": size,
            "header_ascii": ascii_header,
            "warnings": warnings,
        }

    warnings.append("state format is not recognized by V0")
    return {
        "id": "unknown",
        "title": "Unknown state format",
        "confidence": "low",
        "decode_supported": False,
        "address_map": "",
        "size": size,
        "header_ascii": ascii_header,
        "warnings": warnings,
    }


def selected_symbols(
    requested: tuple[str, ...],
    *,
    symbol_table: dict[str, dict[str, Any]],
    max_symbols: int,
) -> list[str]:
    if requested:
        return list(unique_list(requested))[:max_symbols]
    return [symbol for symbol in DEFAULT_SYMBOLS if symbol in symbol_table][:max_symbols]


def read_symbol_values(
    data: bytes,
    *,
    classification: dict[str, Any],
    symbol_table: dict[str, dict[str, Any]],
    symbols: tuple[str, ...],
) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for symbol in symbols:
        entry = symbol_table.get(symbol)
        if entry is None:
            values.append({"symbol": symbol, "status": "missing_symbol"})
            continue
        size = symbol_size(symbol)
        value = read_symbol_bytes(data, classification=classification, entry=entry, size=size)
        record = symbol_record(symbol, entry, size=size)
        if value is None:
            record.update({"status": "unmapped", "value_hex": "", "bytes": []})
        else:
            record.update(
                {
                    "status": "decoded",
                    "value_hex": bytes_hex(value),
                    "bytes": list(value),
                    "little_endian": int.from_bytes(value, "little"),
                }
            )
        values.append(record)
    return values


def symbol_delta_records(
    base_data: bytes,
    other_data: bytes,
    *,
    base_format: dict[str, Any],
    other_format: dict[str, Any],
    symbol_table: dict[str, dict[str, Any]],
    symbols: tuple[str, ...],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for symbol in symbols:
        entry = symbol_table.get(symbol)
        if entry is None:
            continue
        size = symbol_size(symbol)
        before = read_symbol_bytes(base_data, classification=base_format, entry=entry, size=size)
        after = read_symbol_bytes(other_data, classification=other_format, entry=entry, size=size)
        if before is None or after is None or before == after:
            continue
        changed_offsets = [index for index, (left, right) in enumerate(zip(before, after)) if left != right]
        out.append(
            {
                **symbol_record(symbol, entry, size=size),
                "before_hex": bytes_hex(before),
                "after_hex": bytes_hex(after),
                "before_little_endian": int.from_bytes(before, "little"),
                "after_little_endian": int.from_bytes(after, "little"),
                "changed_offsets": changed_offsets,
            }
        )
    return out


def read_symbol_bytes(
    data: bytes,
    *,
    classification: dict[str, Any],
    entry: dict[str, Any],
    size: int,
) -> bytes | None:
    address = int(entry.get("address", 0))
    raw = bytearray()
    for offset in range(size):
        state_offset = address_to_offset(classification, address + offset)
        if state_offset is None or state_offset >= len(data):
            return None
        raw.append(data[state_offset])
    return bytes(raw)


def address_to_offset(classification: dict[str, Any], address: int) -> int | None:
    address &= 0xFFFF
    if classification.get("address_map") == "full_16bit":
        return address
    if classification.get("address_map") == "wram_c000_dfff" and WRAM_START <= address <= WRAM_END:
        return address - WRAM_START
    return None


def address_iter(classification: dict[str, Any]) -> Iterable[int]:
    if classification.get("address_map") == "full_16bit":
        return range(0x10000)
    if classification.get("address_map") == "wram_c000_dfff":
        return range(WRAM_START, WRAM_END + 1)
    return ()


def count_changed_bytes(
    base_data: bytes,
    other_data: bytes,
    *,
    base_format: dict[str, Any],
    other_format: dict[str, Any],
) -> int:
    changed = 0
    for address in set(address_iter(base_format)) & set(address_iter(other_format)):
        base_offset = address_to_offset(base_format, address)
        other_offset = address_to_offset(other_format, address)
        if base_offset is None or other_offset is None:
            continue
        if base_data[base_offset] != other_data[other_offset]:
            changed += 1
    return changed


def address_space_summary(addresses: list[int]) -> dict[str, Any]:
    if not addresses:
        return {"mapped": False, "start": "", "end": "", "address_count": 0}
    return {
        "mapped": True,
        "start": f"{min(addresses):04X}",
        "end": f"{max(addresses):04X}",
        "address_count": len(addresses),
    }


def file_metadata(path: Path, *, data: bytes) -> dict[str, Any]:
    return {
        "path": str(path),
        "size": len(data),
        "sha256": sha256_file(path),
        "suffix": path.suffix.lower(),
    }


def symbol_record(symbol: str, entry: dict[str, Any], *, size: int) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "bank": int(entry.get("bank", 0)),
        "address": int(entry.get("address", 0)),
        "bank_address": str(entry.get("bank_address") or ""),
        "size": size,
        "bank_confidence": "address_slot_only",
    }


def symbol_size(symbol: str) -> int:
    return SYMBOL_SIZES.get(symbol, 1)


def looks_like_vba_sgm(data: bytes) -> bool:
    return len(data) >= 20 and bool(vba_title(data))


def vba_title(data: bytes) -> str:
    if len(data) < 20:
        return ""
    title = data[4:20].split(b"\x00", 1)[0]
    text = printable_ascii(title)
    return text if len(text) >= 4 else ""


def printable_ascii(data: bytes) -> str:
    return "".join(chr(byte) for byte in data if 32 <= byte <= 126).strip()


def bytes_hex(data: bytes) -> str:
    return " ".join(f"{byte:02X}" for byte in data)


def format_inspect_report(report: dict[str, Any]) -> str:
    fmt = report.get("format", {})
    lines = [
        "Save-state inspect",
        f"valid={str(report.get('valid')).lower()} format={fmt.get('id', '')} confidence={fmt.get('confidence', '')}",
        f"state={report.get('state', '')}",
        f"size={report.get('file', {}).get('size', 0)} decode_supported={str(fmt.get('decode_supported')).lower()}",
    ]
    for warning in report.get("warnings", []):
        lines.append(f"warning: {warning}")
    for error in report.get("errors", []):
        lines.append(f"error: {error}")
    symbols = report.get("symbols", [])
    if symbols:
        lines.append("symbols:")
        for item in symbols:
            status = item.get("status", "")
            value = item.get("value_hex", "")
            suffix = f" = {value}" if value else f" ({status})"
            lines.append(f"  {item.get('symbol', '')} {item.get('bank_address', '')}{suffix}")
    return "\n".join(lines)


def format_diff_report(report: dict[str, Any]) -> str:
    lines = [
        "Save-state diff",
        f"valid={str(report.get('valid')).lower()} changed_bytes={report.get('changed_byte_count', 0)} symbol_deltas={report.get('symbol_delta_count', 0)}",
        f"base={report.get('base_state', '')}",
        f"other={report.get('other_state', '')}",
    ]
    for warning in report.get("warnings", []):
        lines.append(f"warning: {warning}")
    for error in report.get("errors", []):
        lines.append(f"error: {error}")
    if report.get("symbol_deltas"):
        lines.append("symbol deltas:")
        for item in report["symbol_deltas"]:
            lines.append(
                f"  {item['symbol']} {item['bank_address']}: {item['before_hex']} -> {item['after_hex']}"
            )
    if report.get("sample_deltas"):
        lines.append("sample byte deltas:")
        for item in report["sample_deltas"][:8]:
            lines.append(f"  ${item['address']}: {item['before_hex']} -> {item['after_hex']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect and diff supported save-state files.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("state")
    inspect_parser.add_argument("--symbols", default="pokegold.sym")
    inspect_parser.add_argument("--symbol", action="append", default=[])
    inspect_parser.add_argument("--max-symbols", type=int, default=32)
    inspect_parser.add_argument("--json", action="store_true")

    diff_parser = subparsers.add_parser("diff")
    diff_parser.add_argument("base_state")
    diff_parser.add_argument("other_state")
    diff_parser.add_argument("--symbols", default="pokegold.sym")
    diff_parser.add_argument("--symbol", action="append", default=[])
    diff_parser.add_argument("--max-deltas", type=int, default=64)
    diff_parser.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "inspect":
        report = build_save_state_inspect_report(
            state_path=args.state,
            symbols_path=args.symbols,
            symbols=tuple(args.symbol),
            max_symbols=args.max_symbols,
        )
        print(json.dumps(report, indent=2, sort_keys=True) if args.json else format_inspect_report(report))
        return 0 if report["valid"] else 1
    if args.command == "diff":
        report = build_save_state_diff_report(
            base_state_path=args.base_state,
            other_state_path=args.other_state,
            symbols_path=args.symbols,
            symbols=tuple(args.symbol),
            max_deltas=args.max_deltas,
        )
        print(json.dumps(report, indent=2, sort_keys=True) if args.json else format_diff_report(report))
        return 0 if report["valid"] else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
