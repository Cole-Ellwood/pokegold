from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .catalog import ROOT
from .provenance import parse_symbol_table, resolve_path


DEFAULT_STORE = "audit/probes.jsonl"
SCHEMA_VERSION = 1


def declare_probe(
    *,
    name: str,
    pc: str,
    bank: int | None = None,
    store_path: str = DEFAULT_STORE,
    symbols_path: str = "pokegold.sym",
    root: Path = ROOT,
) -> dict[str, Any]:
    errors: list[str] = []
    if not name.strip():
        errors.append("--name is required")
    target = resolve_probe_target(pc=pc, bank=bank, symbols_path=symbols_path, root=root)
    if not target["valid"]:
        errors.extend(target["errors"])
    row = {
        "schema_version": SCHEMA_VERSION,
        "event": "declare",
        "name": name.strip(),
        "pc": pc,
        "target": target,
        "declared_at": utc_now(),
    }
    if errors:
        return {
            "schema_version": SCHEMA_VERSION,
            "kind": "unified_debugger_probe_declare",
            "valid": False,
            "errors": errors,
            "probe": row,
            "store": str(resolve_path(store_path, root=root)),
        }
    store = resolve_path(store_path, root=root)
    store.parent.mkdir(parents=True, exist_ok=True)
    with store.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "unified_debugger_probe_declare",
        "valid": True,
        "errors": [],
        "probe": row,
        "store": str(store),
        "active_probe_count": len(active_probes(load_probe_rows(store))),
    }


def resolve_probe_target(*, pc: str, bank: int | None, symbols_path: str, root: Path) -> dict[str, Any]:
    text = pc.strip()
    errors: list[str] = []
    parsed = parse_bank_address(text)
    if parsed is not None:
        target_bank, address = parsed
        if bank is not None and bank != target_bank:
            errors.append(f"--bank {bank:02X} conflicts with banked pc {text}")
        return {
            "valid": not errors,
            "kind": "address",
            "symbol": "",
            "bank": target_bank,
            "address": address,
            "bank_address": f"{target_bank:02X}:{address:04X}",
            "errors": errors,
        }
    address = parse_address(text)
    if address is not None:
        if bank is None:
            errors.append("--bank is required when --pc is an unbanked address")
            target_bank = 0
        else:
            target_bank = bank & 0xFF
        return {
            "valid": not errors,
            "kind": "address",
            "symbol": "",
            "bank": target_bank,
            "address": address,
            "bank_address": f"{target_bank:02X}:{address:04X}",
            "errors": errors,
        }

    symbols = resolve_path(symbols_path, root=root)
    entry = parse_symbol_table(symbols).get(text) if symbols.exists() else None
    if entry:
        target_bank = int(entry.get("bank", 0)) & 0xFF
        target_address = int(entry.get("address", 0)) & 0xFFFF
        return {
            "valid": True,
            "kind": "symbol",
            "symbol": text,
            "bank": target_bank,
            "address": target_address,
            "bank_address": f"{target_bank:02X}:{target_address:04X}",
            "errors": [],
        }
    if bank is not None:
        errors.append(f"could not resolve symbol {text!r} in {symbols_path}")
    return {
        "valid": not errors,
        "kind": "symbol",
        "symbol": text,
        "bank": None,
        "address": None,
        "bank_address": "",
        "errors": errors,
    }


def build_probe_list_report(*, store_path: str = DEFAULT_STORE, root: Path = ROOT) -> dict[str, Any]:
    store = resolve_path(store_path, root=root)
    rows = load_probe_rows(store)
    probes = active_probes(rows)
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "unified_debugger_probe_list",
        "valid": True,
        "store": str(store),
        "row_count": len(rows),
        "active_probe_count": len(probes),
        "probes": sorted(probes.values(), key=lambda item: item["name"]),
        "errors": [],
    }


def build_probe_stats_report(
    *,
    traces: Sequence[str | Path],
    store_path: str = DEFAULT_STORE,
    symbols_path: str = "pokegold.sym",
    root: Path = ROOT,
) -> dict[str, Any]:
    store = resolve_path(store_path, root=root)
    errors: list[str] = []
    if not traces:
        errors.append("at least one --trace is required")
    events: list[dict[str, Any]] = []
    for trace in traces:
        trace_path = Path(trace) if Path(trace).is_absolute() else root / trace
        if not trace_path.exists():
            errors.append(f"missing trace: {trace}")
            continue
        trace_events, trace_errors = load_trace_events(trace_path)
        events.extend(trace_events)
        errors.extend(f"{trace}: {error}" for error in trace_errors)
    summary = active_probe_stats(events=events, store_path=store_path, root=root)
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "unified_debugger_probe_stats",
        "valid": not errors,
        "store": str(store),
        "symbols": str(resolve_path(symbols_path, root=root)),
        "trace_count": len(traces),
        "event_count": len(events),
        "row_count": summary["row_count"],
        "active_probe_count": summary["active_probe_count"],
        "fire_count": summary["fire_count"],
        "stats": summary["stats"],
        "errors": errors,
    }


def active_probe_stats(
    *,
    events: Sequence[Mapping[str, Any]],
    store_path: str = DEFAULT_STORE,
    root: Path = ROOT,
) -> dict[str, Any]:
    store = resolve_path(store_path, root=root)
    rows = load_probe_rows(store)
    probes = active_probes(rows)
    stats = [probe_stats(probe, events) for probe in sorted(probes.values(), key=lambda item: item["name"])]
    return {
        "store": str(store),
        "row_count": len(rows),
        "active_probe_count": len(probes),
        "fire_count": sum(int(item.get("fire_count", 0)) for item in stats),
        "stats": stats,
    }


def reset_probes(*, store_path: str = DEFAULT_STORE, root: Path = ROOT) -> dict[str, Any]:
    store = resolve_path(store_path, root=root)
    row_count = len(load_probe_rows(store))
    store.parent.mkdir(parents=True, exist_ok=True)
    store.write_text("", encoding="utf-8", newline="\n")
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "unified_debugger_probe_reset",
        "valid": True,
        "store": str(store),
        "cleared_row_count": row_count,
        "errors": [],
    }


def load_probe_rows(store: Path) -> list[dict[str, Any]]:
    if not store.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in store.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def active_probes(rows: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    probes: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row.get("event") != "declare":
            continue
        name = str(row.get("name", "")).strip()
        target = row.get("target", {})
        if not name or not isinstance(target, Mapping) or not target.get("valid", False):
            continue
        probes[name] = {
            "name": name,
            "pc": row.get("pc", ""),
            "target": dict(target),
            "declared_at": row.get("declared_at", ""),
        }
    return probes


def probe_stats(probe: Mapping[str, Any], events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    matches = [event for event in events if event_matches_probe(event, probe)]
    frames = [frame for event in matches if (frame := parse_frame(first_present(event, "frame", "frame_index"))) is not None]
    frame_span = "" if not frames else f"{min(frames)}:{max(frames)}"
    intervals = [right - left for left, right in zip(frames, frames[1:])]
    return {
        "name": probe.get("name", ""),
        "target": probe.get("target", {}),
        "fire_count": len(matches),
        "first_frame": None if not frames else min(frames),
        "last_frame": None if not frames else max(frames),
        "frame_span": frame_span,
        "average_inter_fire_interval": None if not intervals else sum(intervals) / len(intervals),
        "first_pc": event_pc(matches[0]).get("bank_address", "") if matches else "",
        "last_pc": event_pc(matches[-1]).get("bank_address", "") if matches else "",
        "sample_matches": [compact_event(event) for event in matches[:8]],
    }


def event_matches_probe(event: Mapping[str, Any], probe: Mapping[str, Any]) -> bool:
    target = probe.get("target", {})
    if not isinstance(target, Mapping):
        return False
    pc = event_pc(event)
    target_bank = target.get("bank")
    target_address = target.get("address")
    if target_bank is not None and target_address is not None:
        if pc.get("bank") == int(target_bank) and pc.get("address") == int(target_address):
            return True
    symbol = str(target.get("symbol") or "")
    label = str(first_present(event, "pc_label", "symbol", "label") or "")
    return bool(symbol and (label == symbol or label.startswith(symbol + "+")))


def event_pc(event: Mapping[str, Any]) -> dict[str, Any]:
    bank_address = first_present(event, "pc_bank_address", "bank_address")
    parsed = parse_bank_address(str(bank_address)) if bank_address is not None else None
    if parsed is not None:
        bank, address = parsed
        return {"bank": bank, "address": address, "bank_address": f"{bank:02X}:{address:04X}"}
    address = parse_address(first_present(event, "pc", "address"))
    bank = parse_int(first_present(event, "bank", "pc_bank"))
    if address is None:
        return {"bank": None, "address": None, "bank_address": ""}
    if bank is None:
        return {"bank": None, "address": address, "bank_address": f"--:{address:04X}"}
    return {"bank": bank & 0xFF, "address": address, "bank_address": f"{bank & 0xFF:02X}:{address:04X}"}


def compact_event(event: Mapping[str, Any]) -> dict[str, Any]:
    pc = event_pc(event)
    return {
        "frame": parse_frame(first_present(event, "frame", "frame_index")),
        "pc": pc["bank_address"],
        "pc_label": first_present(event, "pc_label", "symbol", "label") or "",
        "seq": parse_int(event.get("seq")),
    }


def load_trace_events(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        return [], []
    lines = [line for line in (raw.strip() for raw in text.splitlines()) if line]
    if len(lines) == 1:
        try:
            payload = json.loads(lines[0])
        except json.JSONDecodeError as exc:
            return [], [f"invalid JSON line 1: {exc.msg}"]
        if isinstance(payload, dict):
            if "events" not in payload:
                return [payload], []
            events = payload.get("events", [])
            return ([item for item in events if isinstance(item, dict)] if isinstance(events, list) else [payload]), []
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)], []
        return [], ["single JSON payload must be an object or list"]
    events: list[dict[str, Any]] = []
    errors: list[str] = []
    for line_no, line in enumerate(lines, 1):
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"invalid JSONL line {line_no}: {exc.msg}")
            continue
        if isinstance(event, dict):
            events.append(event)
        else:
            errors.append(f"JSONL line {line_no} is not an object")
    return events, errors


def parse_bank_address(value: str) -> tuple[int, int] | None:
    text = value.strip().replace("$", "").replace("0x", "")
    if ":" not in text:
        return None
    bank_text, _, address_text = text.rpartition(":")
    try:
        return int(bank_text, 16) & 0xFF, int(address_text, 16) & 0xFFFF
    except ValueError:
        return None


def parse_address(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value & 0xFFFF
    text = str(value).strip()
    if not text:
        return None
    if ":" in text:
        parsed = parse_bank_address(text)
        return None if parsed is None else parsed[1]
    text = text.removeprefix("$").removeprefix("0x")
    try:
        return int(text, 16) & 0xFFFF
    except ValueError:
        return None


def parse_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_frame(value: Any) -> int | None:
    return parse_int(value)


def first_present(event: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in event and event[key] is not None:
            return event[key]
    return None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def format_probe_report(report: Mapping[str, Any]) -> str:
    kind = report.get("kind", "")
    if kind == "unified_debugger_probe_declare":
        probe = report.get("probe", {})
        target = probe.get("target", {}) if isinstance(probe, Mapping) else {}
        return "\n".join(
            [
                "Probe declare",
                f"valid={str(report.get('valid')).lower()} name={probe.get('name', '')}",
                f"target={target.get('bank_address', '') or target.get('symbol', '')}",
                *[f"error: {error}" for error in report.get("errors", [])],
            ]
        )
    if kind == "unified_debugger_probe_list":
        lines = ["Probe list", f"active={report.get('active_probe_count', 0)} rows={report.get('row_count', 0)}"]
        for probe in report.get("probes", []):
            target = probe.get("target", {})
            lines.append(f"  {probe.get('name', '')}: {target.get('bank_address', '') or target.get('symbol', '')}")
        return "\n".join(lines)
    if kind == "unified_debugger_probe_stats":
        lines = ["Probe stats", f"valid={str(report.get('valid')).lower()} active={report.get('active_probe_count', 0)}"]
        for error in report.get("errors", []):
            lines.append(f"error: {error}")
        for item in report.get("stats", []):
            lines.append(
                f"  {item.get('name', '')}: fires={item.get('fire_count', 0)} "
                f"frames={item.get('frame_span', '')}"
            )
        return "\n".join(lines)
    if kind == "unified_debugger_probe_reset":
        return f"Probe reset\ncleared_rows={report.get('cleared_row_count', 0)}"
    return json.dumps(report, indent=2, sort_keys=True)


def print_report(report: Mapping[str, Any], *, json_output: bool) -> None:
    print(json.dumps(report, indent=2, sort_keys=True) if json_output else format_probe_report(report))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.debugger.probe",
        description="Declare named PC probes and count probe hits in trace files (P8).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    declare = subparsers.add_parser("declare")
    declare.add_argument("--name", required=True)
    declare.add_argument("--pc", required=True)
    declare.add_argument("--bank", type=lambda text: int(text, 16), default=None)
    declare.add_argument("--symbols", default="pokegold.sym")
    declare.add_argument("--store", default=DEFAULT_STORE)
    declare.add_argument("--json", action="store_true")

    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--store", default=DEFAULT_STORE)
    list_parser.add_argument("--json", action="store_true")

    stats = subparsers.add_parser("stats")
    stats.add_argument("--trace", action="append", default=[])
    stats.add_argument("--symbols", default="pokegold.sym")
    stats.add_argument("--store", default=DEFAULT_STORE)
    stats.add_argument("--json", action="store_true")

    reset = subparsers.add_parser("reset")
    reset.add_argument("--store", default=DEFAULT_STORE)
    reset.add_argument("--json", action="store_true")

    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.command == "declare":
        report = declare_probe(
            name=args.name,
            pc=args.pc,
            bank=args.bank,
            store_path=args.store,
            symbols_path=args.symbols,
        )
        print_report(report, json_output=args.json)
        return 0 if report["valid"] else 1
    if args.command == "list":
        report = build_probe_list_report(store_path=args.store)
        print_report(report, json_output=args.json)
        return 0
    if args.command == "stats":
        report = build_probe_stats_report(
            traces=tuple(args.trace),
            store_path=args.store,
            symbols_path=args.symbols,
        )
        print_report(report, json_output=args.json)
        return 0 if report["valid"] else 1
    if args.command == "reset":
        report = reset_probes(store_path=args.store)
        print_report(report, json_output=args.json)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
