from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.trace import runtime as trace_runtime

from .catalog import ROOT, triage_request
from .ingest import sha256_file
from .provenance import (
    build_provenance_report,
    display_path,
    parse_symbol_table,
    resolve_path,
)
from .slicing import build_slice_report


DEFAULT_ROM = "pokegold.gbc"
DEFAULT_SYMBOLS = "pokegold.sym"


def build_watch_report(
    *,
    watch_symbols: tuple[str, ...],
    rom_path: str = DEFAULT_ROM,
    symbols_path: str = DEFAULT_SYMBOLS,
    save_state: str = "",
    frames: int = 60,
    context_frames: int = 12,
    execute: bool = False,
    root: Path = ROOT,
) -> dict[str, Any]:
    rom = resolve_path(rom_path, root=root)
    sym = resolve_path(symbols_path, root=root)
    save = resolve_path(save_state, root=root) if save_state else None
    errors: list[str] = []
    warnings: list[str] = []
    if frames < 0:
        errors.append("--frames must be non-negative")
    if context_frames < 0:
        errors.append("--context-frames must be non-negative")
    if not watch_symbols:
        errors.append("at least one --watch-symbol is required")
    if not rom.exists():
        errors.append(f"missing ROM: {rom_path}")
    if not sym.exists():
        errors.append(f"missing symbols: {symbols_path}")
    if save is not None and not save.exists():
        errors.append(f"missing save-state: {save_state}")

    symbol_table = parse_symbol_table(sym) if sym.exists() else {}
    watches = [
        build_watch_spec(
            symbol,
            symbol_table,
            symbols_path=sym,
            root=root,
        )
        for symbol in watch_symbols
    ]
    for watch in watches:
        if not watch["found"]:
            errors.append(f"watch symbol not found in symbols: {watch['name']}")

    report = {
        "schema_version": 1,
        "kind": "unified_debugger_watch_report",
        "root": str(root),
        "rom": display_path(rom, root=root),
        "rom_sha256": sha256_file(rom) if rom.exists() else "",
        "symbols": display_path(sym, root=root),
        "symbols_sha256": sha256_file(sym) if sym.exists() else "",
        "save_state": display_path(save, root=root) if save is not None else "",
        "frames": frames,
        "context_frames": context_frames,
        "executed": execute,
        "valid": not errors,
        "hit_count": 0,
        "dynamic_context_event_count": 0,
        "errors": errors,
        "warnings": warnings,
        "watches": watches,
        "events": [],
        "provenance": build_provenance_report(
            symbols_path=str(sym),
            symbols=tuple(watch_symbols),
            max_hits=8,
            root=root,
        ) if sym.exists() else None,
        "known_limits": [
            "This is forward replay with polling plus bounded frame-context snapshots, not hardware watchpoints or reverse execution.",
            "Use trace-index, expectation minimization, or subsystem replay tools for exact cause reduction after a hit.",
        ],
    }
    if errors or not execute:
        return report

    events = execute_watch(
        rom=rom,
        save_state=save,
        watches=watches,
        frames=frames,
        context_frames=context_frames,
        symbol_table=symbol_table,
        symbols_path=sym,
        root=root,
    )
    report["events"] = events
    report["hit_count"] = len(events)
    report["dynamic_context_event_count"] = sum(
        int(event.get("dynamic_context", {}).get("context_frame_count", 0))
        for event in events
    )
    return report


def build_watch_spec(
    symbol: str,
    symbol_table: dict[str, dict[str, Any]],
    *,
    symbols_path: Path,
    root: Path,
) -> dict[str, Any]:
    size = 2 if symbol in {"wCurDamage"} else 1
    entry = symbol_table.get(symbol)
    if entry is None:
        return {
            "name": symbol,
            "found": False,
            "bank": None,
            "address": None,
            "bank_address": "",
            "size": size,
            "triage_match_ids": [],
            "suggested_commands": [],
        }
    provenance = build_provenance_report(
        symbols_path=str(symbols_path),
        symbols=(symbol,),
        max_hits=5,
        root=root,
    )
    symbol_report = provenance["symbols"][0] if provenance["symbols"] else {}
    return {
        "name": symbol,
        "found": True,
        "bank": entry["bank"],
        "address": entry["address"],
        "bank_address": entry["bank_address"],
        "size": size,
        "triage_match_ids": symbol_report.get("triage_match_ids", []),
        "suggested_commands": symbol_report.get("suggested_commands", []),
    }


def execute_watch(
    *,
    rom: Path,
    save_state: Path | None,
    watches: list[dict[str, Any]],
    frames: int,
    context_frames: int,
    symbol_table: dict[str, dict[str, Any]],
    symbols_path: Path,
    root: Path,
) -> list[dict[str, Any]]:
    pyboy = trace_runtime.open_pyboy(
        rom,
        "PyBoy is required for unified debugger watch replay. Import failed",
    )
    trace_runtime.disable_realtime(pyboy)
    try:
        if save_state is not None:
            with save_state.open("rb") as fh:
                pyboy.load_state(fh)
        current = {
            watch["name"]: read_watch_bytes(pyboy, watch)
            for watch in watches
            if watch["found"]
        }
        events: list[dict[str, Any]] = []
        cause_cache: dict[tuple[str, str], dict[str, Any]] = {}
        history: list[dict[str, Any]] = []
        for frame in range(frames + 1):
            pc = int(pyboy.register_file.PC)
            pc_bank = current_pc_bank(pyboy, symbol_table, pc)
            snapshot = runtime_snapshot(
                pyboy=pyboy,
                frame=frame,
                pc=pc,
                pc_bank=pc_bank,
                symbol_table=symbol_table,
                watches=watches,
            )
            for watch in watches:
                if not watch["found"]:
                    continue
                name = watch["name"]
                value = read_watch_bytes(pyboy, watch)
                previous = current[name]
                if value != previous:
                    related_files = related_files_for_watch(
                        name,
                        symbol_table,
                        symbols_path=symbols_path,
                        root=root,
                    )
                    triage = triage_request(changed_files=tuple(related_files), root=root)
                    pc_label = render_pc(symbol_table, pc_bank, pc)
                    cache_key = (name, pc_label)
                    if cache_key not in cause_cache:
                        cause_cache[cache_key] = build_watch_event_cause(
                            watch_symbol=name,
                            pc_label=pc_label,
                            symbols_path=str(symbols_path),
                            root=root,
                        )
                    dynamic_context = build_dynamic_context(
                        history=history,
                        after=snapshot,
                        context_frames=context_frames,
                    )
                    commands = unique_list(
                        [
                            *triage["commands"],
                            *cause_cache[cache_key].get("commands", []),
                            f"python -m tools.debugger trace-index --report <watch_report.json> --watch-symbol {name}",
                            f"python -m tools.debugger explain --report <watch_report.json> --watch-symbol {name}",
                        ]
                    )
                    events.append(
                        {
                            "frame": frame,
                            "watch": name,
                            "old_bytes": list(previous),
                            "new_bytes": list(value),
                            "old_hex": bytes_hex(previous),
                            "new_hex": bytes_hex(value),
                            "pc": pc,
                            "pc_bank": pc_bank,
                            "pc_bank_address": f"{pc_bank:02X}:{pc:04X}",
                            "pc_label": pc_label,
                            "registers": snapshot.get("registers", {}),
                            "dynamic_context": dynamic_context,
                            "source_cause": cause_cache[cache_key],
                            "triage_match_ids": [
                                match["id"] for match in triage["matches"]
                            ],
                            "suggested_commands": triage["commands"],
                            "commands": commands,
                        }
                    )
                    current[name] = value
            history.append(snapshot)
            if len(history) > max(1, context_frames):
                history = history[-max(1, context_frames):]
            if frame < frames:
                pyboy.tick(1, False, False)
        return events
    finally:
        try:
            pyboy.stop(save=False)
        except TypeError:
            pyboy.stop()


def read_watch_bytes(pyboy, watch: dict[str, Any]) -> tuple[int, ...]:
    bank = int(watch["bank"])
    address = int(watch["address"])
    size = int(watch["size"])
    values: list[int] = []
    if 0xD000 <= address <= 0xDFFF and bank:
        try:
            for offset in range(size):
                values.append(int(pyboy.memory[bank, address + offset]))
            return tuple(values)
        except Exception:
            old_bank = int(pyboy.memory[0xFF70])
            pyboy.memory[0xFF70] = bank
            try:
                for offset in range(size):
                    values.append(int(pyboy.memory[address + offset]))
            finally:
                pyboy.memory[0xFF70] = old_bank
            return tuple(values)
    for offset in range(size):
        values.append(int(pyboy.memory[address + offset]))
    return tuple(values)


def current_pc_bank(pyboy, symbol_table: dict[str, dict[str, Any]], pc: int) -> int:
    if pc < 0x4000:
        return 0
    hrom = symbol_table.get("hROMBank")
    if hrom is None:
        return 0
    try:
        return int(pyboy.memory[hrom["address"]])
    except Exception:
        return 0


def runtime_snapshot(
    *,
    pyboy,
    frame: int,
    pc: int,
    pc_bank: int,
    symbol_table: dict[str, dict[str, Any]],
    watches: list[dict[str, Any]],
) -> dict[str, Any]:
    pc_label = render_pc(symbol_table, pc_bank, pc)
    registers = register_snapshot(pyboy)
    return {
        "kind": "runtime_context_frame",
        "event_type": "control_flow",
        "frame": frame,
        "pc": pc,
        "pc_bank": pc_bank,
        "pc_bank_address": f"{pc_bank:02X}:{pc:04X}",
        "pc_label": pc_label,
        "registers": registers,
        **registers,
        "watch_values": {
            watch["name"]: bytes_hex(read_watch_bytes(pyboy, watch))
            for watch in watches
            if watch.get("found")
        },
    }


def register_snapshot(pyboy) -> dict[str, str]:
    registers = {}
    register_file = getattr(pyboy, "register_file", None)
    if register_file is None:
        return registers
    for name in ("A", "F", "B", "C", "D", "E", "H", "L", "SP", "PC"):
        if not hasattr(register_file, name):
            continue
        try:
            value = int(getattr(register_file, name))
        except Exception:
            continue
        width = 4 if name in {"SP", "PC"} else 2
        registers[f"register_{name.lower()}"] = f"{value:0{width}X}"
    return registers


def build_dynamic_context(
    *,
    history: list[dict[str, Any]],
    after: dict[str, Any],
    context_frames: int,
) -> dict[str, Any]:
    limit = max(0, int(context_frames))
    prelude = history[-limit:] if limit else []
    return {
        "sampling": "frame",
        "context_frame_count": len(prelude),
        "prelude": prelude,
        "after": after,
        "known_limits": [
            "This context is sampled once per emulated frame, not once per SM83 instruction.",
        ],
    }


def render_pc(symbol_table: dict[str, dict[str, Any]], bank: int, pc: int) -> str:
    candidates = [
        entry
        for entry in symbol_table.values()
        if int(entry["bank"]) == bank and int(entry["address"]) <= pc
    ]
    if not candidates:
        return f"${bank:02X}:{pc:04X}"
    best = max(candidates, key=lambda entry: int(entry["address"]))
    offset = pc - int(best["address"])
    if offset == 0:
        return str(best["label"])
    if offset <= 0x1000:
        return f"{best['label']}+0x{offset:X}"
    return f"${bank:02X}:{pc:04X}"


def related_files_for_watch(
    symbol: str,
    symbol_table: dict[str, dict[str, Any]],
    *,
    symbols_path: Path,
    root: Path,
) -> list[str]:
    if symbol not in symbol_table:
        return []
    provenance = build_provenance_report(
        symbols_path=str(symbols_path),
        symbols=(symbol,),
        max_hits=5,
        root=root,
    )
    if not provenance["symbols"]:
        return []
    return list(provenance["symbols"][0].get("related_files", []))


def build_watch_event_cause(
    *,
    watch_symbol: str,
    pc_label: str,
    symbols_path: str = DEFAULT_SYMBOLS,
    root: Path = ROOT,
    max_candidates: int = 8,
) -> dict[str, Any]:
    routine = base_runtime_label(pc_label)
    symbols = tuple(unique_list([watch_symbol, routine]))
    if not symbols:
        return empty_watch_event_cause(watch_symbol=watch_symbol, routine=routine)

    slice_report = build_slice_report(
        symbols_path=symbols_path,
        symbols=symbols,
        max_depth=1,
        max_edges=32,
        root=root,
    )
    candidates = source_cause_candidates(
        slice_report=slice_report,
        watch_symbol=watch_symbol,
        routine=routine,
        max_candidates=max_candidates,
    )
    source_files = unique_list(item["source_file"] for item in candidates if item.get("source_file"))
    return {
        "watch": watch_symbol,
        "routine": routine,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "source_files": source_files,
        "commands": watch_cause_commands(
            watch_symbol=watch_symbol,
            routine=routine,
            source_files=source_files,
        ),
        "known_limits": [
            "This is a bounded source-slice cause candidate for a runtime watch hit, not reverse execution.",
            "Confirm the candidate with trace-index, expectation minimization, or the owning subsystem replay when available.",
        ],
    }


def source_cause_candidates(
    *,
    slice_report: dict[str, Any],
    watch_symbol: str,
    routine: str,
    max_candidates: int,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for target in dict_items(slice_report.get("targets")):
        query = str(target.get("query") or target.get("resolved") or "")
        if query == watch_symbol:
            for edge in dict_items(target.get("incoming")):
                candidates.append(
                    source_cause_candidate(
                        edge=edge,
                        watch_symbol=watch_symbol,
                        routine=routine,
                        evidence="incoming reference to watched state",
                    )
                )
        if routine and query == routine:
            for edge in dict_items(target.get("outgoing")):
                if edge.get("target") == watch_symbol:
                    candidates.append(
                        source_cause_candidate(
                            edge=edge,
                            watch_symbol=watch_symbol,
                            routine=routine,
                            evidence="executing routine touches watched state",
                        )
                    )
                elif str(edge.get("access", "")) in {"call", "jump"}:
                    candidates.append(
                        source_cause_candidate(
                            edge=edge,
                            watch_symbol=watch_symbol,
                            routine=routine,
                            evidence="executing routine transfers control near watched state",
                        )
                    )
                elif edge.get("source") == routine:
                    candidates.append(
                        source_cause_candidate(
                            edge=edge,
                            watch_symbol=watch_symbol,
                            routine=routine,
                            evidence="executing routine has adjacent source dependency",
                        )
                    )
    return unique_cause_candidates(candidates)[:max_candidates]


def source_cause_candidate(
    *,
    edge: dict[str, Any],
    watch_symbol: str,
    routine: str,
    evidence: str,
) -> dict[str, Any]:
    access = str(edge.get("access", "reference"))
    source = str(edge.get("source", ""))
    target = str(edge.get("target", ""))
    score = 40
    if target == watch_symbol:
        score += 30
    if source == routine:
        score += 25
    if access == "write":
        score += 30
    elif access in {"reference", "data"}:
        score += 12
    elif access in {"call", "jump"}:
        score += 8
    if edge.get("path"):
        score += 5
    return {
        "score": min(score, 100),
        "routine": routine,
        "source_symbol": source,
        "state_symbol": watch_symbol,
        "target_symbol": target,
        "access": access,
        "source_file": str(edge.get("path", "")),
        "line": edge.get("line"),
        "text": str(edge.get("text", "")),
        "evidence": evidence,
    }


def watch_cause_commands(
    *,
    watch_symbol: str,
    routine: str,
    source_files: list[str],
) -> list[str]:
    commands = []
    symbol_args = f"--symbol {watch_symbol}"
    if routine:
        symbol_args += f" --symbol {routine}"
    commands.append(f"python -m tools.debugger trace-index --symbol {watch_symbol}")
    commands.append(f"python -m tools.debugger slice {symbol_args}")
    commands.append(f"python -m tools.debugger taint --symbol {watch_symbol}")
    if routine:
        commands.append(
            f"python -m tools.debugger trace-instructions --symbol {routine} --watch-symbol {watch_symbol} --execute --out-trace .local\\tmp\\debugger_instruction_trace_{watch_symbol}.jsonl"
        )
    commands.append(f"python -m tools.debugger dynamic-taint --trace <instruction-trace.jsonl> --sink-symbol {watch_symbol} --source-reg <register-or-origin>")
    commands.append(f"python -m tools.debugger explain {symbol_args}")
    if source_files:
        commands.append(
            f"python -m tools.debugger localize --symbol {watch_symbol} --changed-file {source_files[0]}"
        )
        commands.append(
            f"python -m tools.debugger minimize --symbol {watch_symbol} --source-file {source_files[0]}"
        )
    else:
        commands.append(f"python -m tools.debugger minimize --symbol {watch_symbol}")
    return unique_list(commands)


def empty_watch_event_cause(*, watch_symbol: str, routine: str) -> dict[str, Any]:
    return {
        "watch": watch_symbol,
        "routine": routine,
        "candidate_count": 0,
        "candidates": [],
        "source_files": [],
        "commands": watch_cause_commands(
            watch_symbol=watch_symbol,
            routine=routine,
            source_files=[],
        ),
        "known_limits": [
            "No symbol context was available for source-cause slicing.",
        ],
    }


def unique_cause_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, Any, str, str, str]] = set()
    for item in sorted(candidates, key=lambda candidate: (-int(candidate["score"]), str(candidate.get("source_file", "")))):
        key = (
            str(item.get("source_file", "")),
            item.get("line"),
            str(item.get("source_symbol", "")),
            str(item.get("target_symbol", "")),
            str(item.get("access", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def base_runtime_label(label: str) -> str:
    text = str(label).strip()
    if not text or text.startswith("$"):
        return ""
    if "+" in text:
        text = text.split("+", 1)[0]
    if ":" in text and text[:2].isalnum():
        return ""
    return text


def bytes_hex(values: tuple[int, ...]) -> str:
    return "".join(f"{value & 0xFF:02X}" for value in values)


def dict_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [item for item in value if isinstance(item, dict)]


def unique_list(values: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value)
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out
