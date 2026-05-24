from __future__ import annotations

import shutil
import tempfile
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
DEFAULT_RESET_SENTINEL_SYMBOLS = ("Start", "Reset", "_Start")
DEFAULT_RESET_SENTINEL_ADDRESSES = (
    ("reset_vector", 0, 0x0000),
    ("entry_vector", 0, 0x0100),
)
WORD_WATCH_SYMBOLS = {
    "wCurDamage",
    "wScriptPos",
    "wScriptAfterPointer",
    "wQueuedScriptAddr",
    "wDeferredScriptAddr",
    "wMapScriptsPointer",
}
SCRIPT_MODE_NAMES = {
    0: "off",
    1: "read",
    2: "wait_movement",
    3: "wait",
}
RESET_CONTEXT_SYMBOLS = (
    "hROMBank",
    "hWRAMBank",
    "wBattleMode",
    "wTempWildMonSpecies",
)
BUTTON_NAMES = {"a", "b", "start", "select", "up", "down", "left", "right"}


def build_watch_report(
    *,
    watch_symbols: tuple[str, ...],
    rom_path: str = DEFAULT_ROM,
    symbols_path: str = DEFAULT_SYMBOLS,
    save_state: str = "",
    battery_save: str = "",
    boot_continue: bool = False,
    input_events: tuple[str, ...] = (),
    out_initial_state: str = "",
    frames: int = 60,
    context_frames: int = 12,
    execute: bool = False,
    reset_sentinel: bool = False,
    sentinel_symbols: tuple[str, ...] = (),
    root: Path = ROOT,
) -> dict[str, Any]:
    rom = resolve_path(rom_path, root=root)
    sym = resolve_path(symbols_path, root=root)
    save = resolve_path(save_state, root=root) if save_state else None
    battery = resolve_path(battery_save, root=root) if battery_save else None
    initial_state = resolve_path(out_initial_state, root=root) if out_initial_state else None
    errors: list[str] = []
    warnings: list[str] = []
    if frames < 0:
        errors.append("--frames must be non-negative")
    if context_frames < 0:
        errors.append("--context-frames must be non-negative")
    if not watch_symbols and not reset_sentinel:
        errors.append("at least one --watch-symbol or --reset-sentinel is required")
    if not rom.exists():
        errors.append(f"missing ROM: {rom_path}")
    if not sym.exists():
        errors.append(f"missing symbols: {symbols_path}")
    if save is not None and not save.exists():
        errors.append(f"missing save-state: {save_state}")
    if battery is not None and not battery.exists():
        errors.append(f"missing battery save: {battery_save}")
    if save is not None and battery is not None:
        errors.append("--save-state and --battery-save are mutually exclusive")
    input_plan, input_errors = parse_input_events(input_events)
    errors.extend(input_errors)
    effective_boot_continue = boot_continue or battery is not None

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
    sentinel_targets = build_reset_sentinel_targets(
        symbol_table,
        sentinel_symbols=sentinel_symbols,
    ) if reset_sentinel else []

    report = {
        "schema_version": 1,
        "kind": "unified_debugger_watch_report",
        "root": str(root),
        "rom": display_path(rom, root=root),
        "rom_sha256": sha256_file(rom) if rom.exists() else "",
        "symbols": display_path(sym, root=root),
        "symbols_sha256": sha256_file(sym) if sym.exists() else "",
        "save_state": display_path(save, root=root) if save is not None else "",
        "battery_save": display_path(battery, root=root) if battery is not None else "",
        "boot_continue": effective_boot_continue,
        "out_initial_state": display_path(initial_state, root=root) if initial_state is not None else "",
        "input_events": input_plan,
        "frames": frames,
        "context_frames": context_frames,
        "executed": execute,
        "reset_sentinel": reset_sentinel,
        "reset_context_symbols": list(RESET_CONTEXT_SYMBOLS),
        "sentinel_targets": sentinel_targets,
        "valid": not errors,
        "hit_count": 0,
        "reset_event_count": 0,
        "script_state_event_count": 0,
        "dynamic_context_event_count": 0,
        "runtime_summary": {},
        "errors": errors,
        "warnings": warnings,
        "watches": watches,
        "events": [],
        "reset_events": [],
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

    events, reset_events, execution_errors, runtime_summary = execute_watch(
        rom=rom,
        save_state=save,
        battery_save=battery,
        boot_continue=effective_boot_continue,
        input_plan=input_plan,
        out_initial_state=initial_state,
        watches=watches,
        frames=frames,
        context_frames=context_frames,
        symbol_table=symbol_table,
        symbols_path=sym,
        reset_sentinel=reset_sentinel,
        sentinel_targets=sentinel_targets,
        root=root,
    )
    report["errors"].extend(execution_errors)
    report["valid"] = not report["errors"]
    report["runtime_summary"] = runtime_summary
    report["events"] = events
    report["reset_events"] = reset_events
    report["hit_count"] = len(events)
    report["reset_event_count"] = len(reset_events)
    report["script_state_event_count"] = sum(
        1 for event in events if event.get("event_type") == "invalid_script_state"
    )
    report["dynamic_context_event_count"] = sum(
        int(event.get("dynamic_context", {}).get("context_frame_count", 0))
        for event in events
    ) + sum(
        int(event.get("dynamic_context", {}).get("context_frame_count", 0))
        for event in reset_events
    )
    return report


def build_watch_spec(
    symbol: str,
    symbol_table: dict[str, dict[str, Any]],
    *,
    symbols_path: Path,
    root: Path,
) -> dict[str, Any]:
    size = 2 if symbol in WORD_WATCH_SYMBOLS else 1
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
    battery_save: Path | None,
    boot_continue: bool,
    input_plan: list[dict[str, Any]],
    out_initial_state: Path | None,
    watches: list[dict[str, Any]],
    frames: int,
    context_frames: int,
    symbol_table: dict[str, dict[str, Any]],
    symbols_path: Path,
    reset_sentinel: bool,
    sentinel_targets: list[dict[str, Any]],
    root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str], dict[str, Any]]:
    temp_dir: tempfile.TemporaryDirectory[str] | None = None
    work_rom = rom
    if battery_save is not None:
        temp_dir = tempfile.TemporaryDirectory(prefix="debugger_watch_")
        work_rom = Path(temp_dir.name) / rom.name
        shutil.copy2(rom, work_rom)
        shutil.copy2(battery_save, work_rom.with_suffix(work_rom.suffix + ".ram"))
    pyboy = trace_runtime.open_pyboy(
        work_rom,
        "PyBoy is required for unified debugger watch replay. Import failed",
    )
    trace_runtime.disable_realtime(pyboy)
    rom_bank_count = max(1, (rom.stat().st_size + 0x3FFF) // 0x4000) if rom.exists() else 0
    hooked: list[tuple[int, int]] = []
    try:
        if save_state is not None:
            with save_state.open("rb") as fh:
                pyboy.load_state(fh)
        if boot_continue:
            press_continue(pyboy)
        if out_initial_state is not None:
            out_initial_state.parent.mkdir(parents=True, exist_ok=True)
            with out_initial_state.open("wb") as fh:
                pyboy.save_state(fh)
        reset_events: list[dict[str, Any]] = []
        execution_errors: list[str] = []
        current_frame = 0
        history: list[dict[str, Any]] = []
        input_events_by_frame = group_input_events(input_plan)
        applied_inputs: list[dict[str, Any]] = []
        if reset_sentinel:
            if not hasattr(pyboy, "hook_register"):
                execution_errors.append("reset sentinel requires PyBoy hook_register support")
            else:
                for target in sentinel_targets:
                    bank = int(target["bank"])
                    pc = int(target["address"])

                    def make_reset_callback(row: dict[str, Any]):
                        def callback(_ctx: Any) -> None:
                            snapshot = runtime_snapshot(
                                pyboy=pyboy,
                                frame=current_frame,
                                pc=int(row["address"]),
                                pc_bank=int(row["bank"]),
                                symbol_table=symbol_table,
                                watches=watches,
                            )
                            reset_events.append(
                                {
                                    "event_type": "reset_sentinel",
                                    "frame": current_frame,
                                    "target": dict(row),
                                    "pc": int(row["address"]),
                                    "pc_bank": int(row["bank"]),
                                    "pc_bank_address": row["bank_address"],
                                    "pc_label": render_pc(
                                        symbol_table,
                                        int(row["bank"]),
                                        int(row["address"]),
                                    ),
                                    "registers": snapshot.get("registers", {}),
                                    "context_symbols": read_context_symbols(pyboy, symbol_table),
                                    "dynamic_context": build_dynamic_context(
                                        history=history,
                                        after=snapshot,
                                        context_frames=context_frames,
                                    ),
                                    "commands": [
                                        "python -m tools.debugger trace-index --report <reset-watch.json>",
                                        "python -m tools.debugger wram-bank-hazards --source-file <suspect.asm>",
                                        "python -m tools.debugger trace-instructions --report <reset-watch.json> --execute --require-hit",
                                    ],
                                }
                            )
                        return callback

                    try:
                        pyboy.hook_register(bank, pc, make_reset_callback(target), None)
                        hooked.append((bank, pc))
                    except Exception as exc:
                        execution_errors.append(
                            f"reset sentinel hook failed for {target['bank_address']} {target['name']}: {exc}"
                        )
        current = {
            watch["name"]: read_watch_bytes(pyboy, watch)
            for watch in watches
            if watch["found"]
        }
        events: list[dict[str, Any]] = []
        cause_cache: dict[tuple[str, str], dict[str, Any]] = {}
        seen_invalid_script_states: set[tuple[int, int, int, int]] = set()
        initial_snapshot: dict[str, Any] = {}
        final_snapshot: dict[str, Any] = {}
        for frame in range(frames + 1):
            current_frame = frame
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
            if frame == 0:
                initial_snapshot = snapshot
            final_snapshot = snapshot
            invalid_script = detect_invalid_script_state(
                pyboy=pyboy,
                symbol_table=symbol_table,
                rom_bank_count=rom_bank_count,
            )
            if invalid_script:
                signature = (
                    int(invalid_script["bank"]),
                    int(invalid_script["pos"]),
                    int(invalid_script["mode"]),
                    int(invalid_script["running"]),
                )
                if signature not in seen_invalid_script_states:
                    seen_invalid_script_states.add(signature)
                    dynamic_context = build_dynamic_context(
                        history=history,
                        after=snapshot,
                        context_frames=context_frames,
                    )
                    events.append(
                        {
                            "event_type": "invalid_script_state",
                            "frame": frame,
                            "watch": "script_state",
                            "pc": pc,
                            "pc_bank": pc_bank,
                            "pc_bank_address": f"{pc_bank:02X}:{pc:04X}",
                            "pc_label": render_pc(symbol_table, pc_bank, pc),
                            "registers": snapshot.get("registers", {}),
                            "dynamic_context": dynamic_context,
                            "script": invalid_script["bank_address"],
                            "bank": invalid_script["bank"],
                            "pos": invalid_script["pos"],
                            "mode": invalid_script["mode"],
                            "running": invalid_script["running"],
                            "reasons": invalid_script["reasons"],
                            "commands": [
                                "python -m tools.debugger script-resume-gate --report <watch_report.json>",
                                "python -m tools.debugger wram-ownership --symbol wSeenTrainerBank --symbol wScriptAfterPointer --symbol wRunningTrainerBattleScript",
                                "python -m tools.debugger trace-instructions --symbol Script_startbattle --symbol EvolveAfterBattle --symbol Script_scripttalkafter --watch-symbol wScriptBank --watch-symbol wScriptPos --execute --require-hit",
                            ],
                        }
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
            for input_event in input_events_by_frame.get(frame, []):
                pyboy.button(str(input_event["button"]), delay=int(input_event["delay"]))
                applied_inputs.append(dict(input_event))
            history.append(snapshot)
            if len(history) > max(1, context_frames):
                history = history[-max(1, context_frames):]
            if frame < frames:
                current_frame = frame + 1
                pyboy.tick(1, False, False)
        return (
            events,
            reset_events,
            execution_errors,
            {
                "frame_count": frames + 1,
                "battery_save_booted": battery_save is not None,
                "boot_continue": boot_continue,
                "out_initial_state": display_path(out_initial_state, root=root) if out_initial_state is not None else "",
                "applied_input_count": len(applied_inputs),
                "applied_inputs": applied_inputs[:64],
                "initial": compact_runtime_snapshot(initial_snapshot),
                "final": compact_runtime_snapshot(final_snapshot),
            },
        )
    finally:
        for bank, pc in hooked:
            try:
                pyboy.hook_deregister(bank, pc)
            except Exception:
                pass
        try:
            pyboy.stop(save=False)
        except TypeError:
            pyboy.stop()
        if temp_dir is not None:
            temp_dir.cleanup()


def parse_input_events(raw_events: tuple[str, ...]) -> tuple[list[dict[str, Any]], list[str]]:
    events: list[dict[str, Any]] = []
    errors: list[str] = []
    for raw in raw_events:
        for item in raw.split(","):
            text = item.strip()
            if not text:
                continue
            parts = text.split(":")
            if len(parts) not in {2, 3}:
                errors.append(f"invalid input event, expected FRAME:BUTTON[:DELAY]: {text}")
                continue
            try:
                frame = int(parts[0], 0)
            except ValueError:
                errors.append(f"invalid input frame in event: {text}")
                continue
            button = parts[1].strip().lower()
            delay = 8
            if len(parts) == 3:
                try:
                    delay = int(parts[2], 0)
                except ValueError:
                    errors.append(f"invalid input delay in event: {text}")
                    continue
            if frame < 0:
                errors.append(f"input frame must be nonnegative: {text}")
                continue
            if delay < 0:
                errors.append(f"input delay must be nonnegative: {text}")
                continue
            if button not in BUTTON_NAMES:
                errors.append(f"unknown input button {button!r} in event: {text}")
                continue
            events.append({"frame": frame, "button": button, "delay": delay, "source": text})
    events.sort(key=lambda event: (int(event["frame"]), str(event["button"])))
    return events, unique_list(errors)


def group_input_events(events: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = {}
    for event in events:
        grouped.setdefault(int(event["frame"]), []).append(event)
    return grouped


def press_continue(pyboy) -> None:
    pyboy.tick(1800, False, False)
    for button in ("start", "a", "a", "a"):
        pyboy.button(button, delay=8)
        pyboy.tick(180, False, False)


def compact_runtime_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    if not snapshot:
        return {}
    return {
        "frame": snapshot.get("frame"),
        "pc_bank_address": snapshot.get("pc_bank_address", ""),
        "pc_label": snapshot.get("pc_label", ""),
        "registers": snapshot.get("registers", {}),
        "watch_values": snapshot.get("watch_values", {}),
    }


def detect_invalid_script_state(
    *,
    pyboy,
    symbol_table: dict[str, dict[str, Any]],
    rom_bank_count: int,
) -> dict[str, Any] | None:
    required = ("wScriptBank", "wScriptPos", "wScriptMode", "wScriptRunning")
    if any(symbol not in symbol_table for symbol in required):
        return None
    bank = read_symbol_int(pyboy, symbol_table, "wScriptBank", 1)
    pos = read_symbol_int(pyboy, symbol_table, "wScriptPos", 2)
    mode = read_symbol_int(pyboy, symbol_table, "wScriptMode", 1)
    running = read_symbol_int(pyboy, symbol_table, "wScriptRunning", 1)
    if bank is None or pos is None or mode is None or running is None:
        return None
    if not running and mode == 0:
        return None
    reasons: list[str] = []
    if mode not in SCRIPT_MODE_NAMES:
        reasons.append(f"script mode {mode} is outside known script modes")
    if rom_bank_count and bank >= rom_bank_count:
        reasons.append(f"script bank ${bank:02X} is outside ROM bank count {rom_bank_count}")
    if bank and pos < 0x4000:
        reasons.append(f"banked script pointer ${bank:02X}:${pos:04X} points below the switchable ROM window")
    if pos == 0:
        reasons.append("script pointer is null")
    if not reasons:
        return None
    return {
        "bank": bank,
        "pos": pos,
        "mode": mode,
        "running": running,
        "bank_address": f"{bank:02X}:{pos:04X}",
        "reasons": reasons,
    }


def read_symbol_int(
    pyboy,
    symbol_table: dict[str, dict[str, Any]],
    symbol: str,
    size: int,
) -> int | None:
    entry = symbol_table.get(symbol)
    if entry is None:
        return None
    watch = {
        "name": symbol,
        "found": True,
        "bank": entry["bank"],
        "address": entry["address"],
        "size": size,
    }
    values = read_watch_bytes(pyboy, watch)
    if size == 1:
        return values[0]
    return values[0] | (values[1] << 8)


def build_reset_sentinel_targets(
    symbol_table: dict[str, dict[str, Any]],
    *,
    sentinel_symbols: tuple[str, ...] = (),
) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    for name, bank, address in DEFAULT_RESET_SENTINEL_ADDRESSES:
        targets.append(
            {
                "name": name,
                "found": True,
                "source": "default_address",
                "bank": bank,
                "address": address,
                "bank_address": f"{bank:02X}:{address:04X}",
            }
        )
    for symbol in unique_list([*DEFAULT_RESET_SENTINEL_SYMBOLS, *sentinel_symbols]):
        entry = symbol_table.get(symbol)
        if entry is None:
            continue
        target = {
            "name": symbol,
            "found": True,
            "source": "symbol",
            "bank": int(entry["bank"]),
            "address": int(entry["address"]),
            "bank_address": entry["bank_address"],
        }
        key = (target["bank"], target["address"])
        if key in {(int(item["bank"]), int(item["address"])) for item in targets}:
            continue
        targets.append(target)
    return targets


def read_context_symbols(pyboy, symbol_table: dict[str, dict[str, Any]]) -> dict[str, str]:
    values: dict[str, str] = {}
    for symbol in RESET_CONTEXT_SYMBOLS:
        entry = symbol_table.get(symbol)
        if entry is None:
            continue
        watch = {
            "name": symbol,
            "found": True,
            "bank": entry["bank"],
            "address": entry["address"],
            "size": 1,
        }
        try:
            values[symbol] = bytes_hex(read_watch_bytes(pyboy, watch))
        except Exception as exc:
            values[symbol] = f"unreadable:{exc}"
    return values


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
