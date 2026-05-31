from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from tools.trace import runtime as rt

from .catalog import ROOT
from .content_mirror.audio import parse_channel_blocks
from .content_mirror.scripts import parse_script_blocks
from .navigate import (
    DEFAULT_ROM,
    DEFAULT_SYMBOLS,
    describe_state,
    navigate_to,
    observe,
    parse_pokemon_names,
    parse_trainer_class_names,
)
from .provenance import display_path, parse_symbol_table, resolve_path
from .runtime_state import load_map_catalog
from . import state_predicate
from .taint import build_taint_report
from .visual_snapshot import build_visual_snapshot_report


Navigator = Callable[..., dict[str, Any]]


def sha256_bytes(data: bytes) -> str:
    import hashlib

    return hashlib.sha256(data).hexdigest()


def resolve_byte_target(byte: str, *, symbols_path: str, root: Path = ROOT) -> dict[str, Any]:
    sym_path = resolve_path(symbols_path, root=root)
    table = parse_symbol_table(sym_path) if sym_path.exists() else {}
    raw = byte.strip()
    errors: list[str] = []
    if not raw:
        errors.append("--byte must not be empty")
        return {"raw": raw, "valid": False, "errors": errors}
    if raw.startswith("$"):
        try:
            address = int(raw[1:], 16)
        except ValueError:
            errors.append(f"invalid hex byte target: {raw}")
            return {"raw": raw, "valid": False, "errors": errors}
        symbol = first_symbol_at_address(table, address)
        return {
            "raw": raw,
            "valid": True,
            "address": address,
            "address_hex": f"${address:04X}",
            "symbol": symbol,
            "target_kind": "address",
        }
    entry = table.get(raw)
    if entry is None:
        errors.append(f"symbol not found in {symbols_path}: {raw}")
        return {"raw": raw, "valid": False, "errors": errors, "target_kind": "symbol"}
    return {
        "raw": raw,
        "valid": True,
        "address": int(entry.get("address", 0)),
        "address_hex": f"${int(entry.get('address', 0)):04X}",
        "bank": int(entry.get("bank", 0)),
        "symbol": raw,
        "target_kind": "symbol",
        "source": entry.get("source", ""),
    }


def first_symbol_at_address(table: dict[str, dict[str, Any]], address: int) -> str:
    preferred = ("wCurDamage", "wBattleMode", "wPlayerTurnsTaken", "wScriptPos")
    matches = [
        name
        for name, entry in table.items()
        if int(entry.get("address", -1)) == address
    ]
    for name in preferred:
        if name in matches:
            return name
    return sorted(matches)[0] if matches else ""


def build_auto_taint_report(
    *,
    byte: str,
    at: str,
    rom_path: str = str(DEFAULT_ROM),
    symbols_path: str = str(DEFAULT_SYMBOLS),
    root: Path = ROOT,
    navigator: Navigator = navigate_to,
) -> dict[str, Any]:
    target = resolve_byte_target(byte, symbols_path=symbols_path, root=root)
    navigation = run_navigation(at, rom_path=rom_path, symbols_path=symbols_path, navigator=navigator)
    errors = [*target.get("errors", []), *navigation.get("errors", [])]
    source_symbol = target.get("symbol") or ""
    static_taint = None
    if source_symbol:
        static_taint = build_taint_report(symbols_path=symbols_path, symbols=(source_symbol,), root=root)
        errors.extend(static_taint.get("errors", []))
    else:
        errors.append(f"no symbol could be resolved for byte target {byte!r}")

    valid = not errors and bool(navigation.get("reached"))
    chain = build_taint_chain(target=target, navigation=navigation, static_taint=static_taint)
    return {
        "schema_version": 1,
        "kind": "debugger_deity_auto_taint",
        "root": str(root),
        "valid": valid,
        "proof_status": "taint_proven" if valid else "blocked_by_navigation_or_target",
        "evidence_marker": "taint chain",
        "byte": byte,
        "target": target,
        "at": at,
        "navigation": navigation,
        "static_taint": static_taint,
        "taint_chain": chain,
        "error_count": len(errors),
        "errors": errors,
        "known_limits": [
            "This first auto-taint surface resolves the target byte, self-navigates to the requested state, and attaches the existing source-level taint chain.",
            "Instruction-window auto-capture is still the remaining Phase 2 depth work; the command fails closed when exact navigation is unavailable.",
        ],
    }


def build_taint_chain(
    *,
    target: dict[str, Any],
    navigation: dict[str, Any],
    static_taint: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    chain: list[dict[str, Any]] = []
    if navigation.get("reached"):
        chain.append(
            {
                "kind": "auto_navigation",
                "checkpoint": navigation.get("checkpoint", ""),
                "state": navigation.get("state_path", ""),
                "manifest": navigation.get("manifest_path", ""),
                "observed": navigation.get("map_desc", ""),
            }
        )
    if target.get("symbol"):
        chain.append(
            {
                "kind": "byte_target",
                "symbol": target.get("symbol"),
                "address": target.get("address_hex"),
            }
        )
    if static_taint:
        paths = static_taint.get("paths", [])
        if paths:
            chain.append({"kind": "source_taint_path", "path": paths[0]})
    return chain


def build_auto_replay_report(
    *,
    surface: str,
    at: str,
    rom_path: str = str(DEFAULT_ROM),
    symbols_path: str = str(DEFAULT_SYMBOLS),
    frames: int = 120,
    root: Path = ROOT,
    navigator: Navigator = navigate_to,
) -> dict[str, Any]:
    if surface == "audio":
        species = cry_species_from_predicate(at)
        if species:
            return build_audio_cry_replay_report(
                species=species,
                at=at,
                rom_path=rom_path,
                symbols_path=symbols_path,
                frames=frames,
                root=root,
                navigator=navigator,
            )
    if surface == "graphics":
        return build_graphics_replay_report(
            at=at,
            rom_path=rom_path,
            symbols_path=symbols_path,
            frames=frames,
            root=root,
            navigator=navigator,
        )
    if surface == "script":
        script_label = script_label_from_predicate(at)
        if script_label:
            return build_script_vm_replay_report(
                script_label=script_label,
                at=at,
                rom_path=rom_path,
                symbols_path=symbols_path,
                frames=frames,
                root=root,
                navigator=navigator,
            )

    navigation = run_navigation(at, rom_path=rom_path, symbols_path=symbols_path, navigator=navigator)
    errors = [*navigation.get("errors", [])]
    if surface not in {"audio", "graphics", "script"}:
        errors.append(f"unsupported replay surface: {surface}")
    replay = None
    if navigation.get("reached"):
        replay = collect_runtime_digest(
            state_path=navigation.get("state_path", ""),
            rom_path=navigation.get("rom", rom_path),
            symbols_path=navigation.get("symbols", symbols_path),
            frames=frames,
            root=root,
        )
        errors.extend(replay.get("errors", []))
    valid = not errors and bool(replay)
    return {
        "schema_version": 1,
        "kind": "debugger_deity_surface_replay",
        "root": str(root),
        "valid": valid,
        "proof_status": "replay_diff_captured" if valid else "blocked_by_navigation",
        "evidence_marker": "replay diff",
        "surface": surface,
        "at": at,
        "navigation": navigation,
        "runtime_replay": replay,
        "error_count": len(errors),
        "errors": errors,
        "known_limits": [
            "This headless replay packet captures runtime RAM/frame digests from an auto-reached state.",
            "Surface-specific APU/VRAM/script semantic diffing remains the next Phase 3 depth layer after exact navigation is available.",
        ],
    }


def build_audio_cry_replay_report(
    *,
    species: str,
    at: str,
    rom_path: str,
    symbols_path: str,
    frames: int,
    root: Path,
    navigator: Navigator,
) -> dict[str, Any]:
    navigation = run_navigation("map=PLAYERS_HOUSE_2F", rom_path=rom_path, symbols_path=symbols_path, navigator=navigator)
    errors = [*navigation.get("errors", [])]
    static_cry = static_cry_decode(species, root=root)
    errors.extend(static_cry.get("errors", []))
    runtime = None
    if navigation.get("reached") and static_cry.get("valid"):
        runtime = collect_cry_apu_timeline(
            state_path=navigation.get("state_path", ""),
            rom_path=navigation.get("rom", rom_path),
            symbols_path=navigation.get("symbols", symbols_path),
            species=species,
            frames=frames,
            root=root,
        )
        errors.extend(runtime.get("errors", []))
    diff = audio_replay_diff(static_cry=static_cry, runtime=runtime)
    valid = not errors and bool(diff.get("valid"))
    return {
        "schema_version": 1,
        "kind": "debugger_deity_surface_replay",
        "root": str(root),
        "valid": valid,
        "proof_status": "replay_diff_captured" if valid else "blocked_by_audio_replay",
        "evidence_marker": "replay diff",
        "surface": "audio",
        "at": at,
        "navigation": navigation,
        "static_mirror": static_cry,
        "runtime_replay": runtime,
        "replay_diff": diff,
        "error_count": len(errors),
        "errors": errors,
        "known_limits": [
            "The cry context is materialized from an auto-reached save state by entering the ROM's PlayCry routine with the selected species index.",
            "The diff currently checks source-declared cry channels against an emulator-observed APU register timeline and digest; it does not claim analog mixer fidelity.",
        ],
    }


def build_graphics_replay_report(
    *,
    at: str,
    rom_path: str,
    symbols_path: str,
    frames: int,
    root: Path,
    navigator: Navigator,
) -> dict[str, Any]:
    navigation = run_navigation(at, rom_path=rom_path, symbols_path=symbols_path, navigator=navigator)
    errors = [*navigation.get("errors", [])]
    snapshot = None
    if navigation.get("reached"):
        snapshot = build_visual_snapshot_report(
            rom_path=navigation.get("rom", rom_path),
            symbols_path=navigation.get("symbols", symbols_path),
            save_state=navigation.get("state_path", ""),
            frames=0,
            execute=True,
            root=root,
        )
        errors.extend(snapshot.get("errors", []))
    diff = graphics_replay_diff(snapshot=snapshot, at=at, root=root)
    valid = not errors and bool(diff.get("valid"))
    return {
        "schema_version": 1,
        "kind": "debugger_deity_surface_replay",
        "root": str(root),
        "valid": valid,
        "proof_status": "replay_diff_captured" if valid else "blocked_by_graphics_replay",
        "evidence_marker": "replay diff",
        "surface": "graphics",
        "at": at,
        "navigation": navigation,
        "runtime_replay": snapshot,
        "replay_diff": diff,
        "error_count": len(errors),
        "errors": errors,
        "known_limits": [
            "Graphics replay captures PyBoy framebuffer, VRAM, OAM, and LCD register digests from the auto-reached state.",
            "The current mirror comparison is digest-level against source-resolved map identity, not a full tile-by-tile renderer parity proof.",
        ],
    }


def build_script_vm_replay_report(
    *,
    script_label: str,
    at: str,
    rom_path: str,
    symbols_path: str,
    frames: int,
    root: Path,
    navigator: Navigator,
) -> dict[str, Any]:
    base_predicate = predicate_without_fields(at, {"script"}) or "map=ELMS_LAB"
    navigation = run_navigation(base_predicate, rom_path=rom_path, symbols_path=symbols_path, navigator=navigator)
    errors = [*navigation.get("errors", [])]
    static_script = static_script_decode(script_label, root=root)
    errors.extend(static_script.get("errors", []))
    runtime = None
    if navigation.get("reached") and static_script.get("valid"):
        runtime = collect_script_vm_stream(
            state_path=navigation.get("state_path", ""),
            rom_path=navigation.get("rom", rom_path),
            symbols_path=navigation.get("symbols", symbols_path),
            script_label=script_label,
            frames=frames,
            root=root,
        )
        errors.extend(runtime.get("errors", []))
    diff = script_replay_diff(static_script=static_script, runtime=runtime)
    valid = not errors and bool(diff.get("valid"))
    return {
        "schema_version": 1,
        "kind": "debugger_deity_surface_replay",
        "root": str(root),
        "valid": valid,
        "proof_status": "replay_diff_captured" if valid else "blocked_by_script_replay",
        "evidence_marker": "replay diff",
        "surface": "script",
        "at": at,
        "navigation": navigation,
        "static_mirror": static_script,
        "runtime_replay": runtime,
        "replay_diff": diff,
        "error_count": len(errors),
        "errors": errors,
        "known_limits": [
            "Script replay patches the same script-runner WRAM fields CallScript installs, on top of the auto-reached map context.",
            "The diff checks script pointer progression against the static decoded command stream; deeper branch-value attribution remains instruction-trace work.",
        ],
    }


def build_live_view_report(
    *,
    at: str,
    frames: int,
    rom_path: str = str(DEFAULT_ROM),
    symbols_path: str = str(DEFAULT_SYMBOLS),
    snapshot: str = "",
    root: Path = ROOT,
    navigator: Navigator = navigate_to,
) -> dict[str, Any]:
    navigation = run_navigation(at, rom_path=rom_path, symbols_path=symbols_path, navigator=navigator)
    errors = [*navigation.get("errors", [])]
    stream = None
    if navigation.get("reached"):
        stream = collect_runtime_stream(
            state_path=navigation.get("state_path", ""),
            rom_path=navigation.get("rom", rom_path),
            symbols_path=navigation.get("symbols", symbols_path),
            frames=frames,
            root=root,
        )
        errors.extend(stream.get("errors", []))
    snapshot_path = ""
    if snapshot and stream is not None:
        path = resolve_path(snapshot, root=root)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(stream, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        snapshot_path = display_path(path, root=root)
    valid = not errors and stream is not None
    return {
        "schema_version": 1,
        "kind": "debugger_deity_live_view",
        "root": str(root),
        "valid": valid,
        "proof_status": "live_stream_started" if valid else "blocked_by_navigation",
        "evidence_marker": "per-frame state",
        "at": at,
        "frames": frames,
        "navigation": navigation,
        "stream": stream,
        "snapshot": snapshot_path,
        "error_count": len(errors),
        "errors": errors,
        "known_limits": [
            "This is the headless JSON stream substrate for the live view.",
            "Interactive TUI/canvas rendering remains a later Phase 5 presentation layer.",
        ],
    }


def cry_species_from_predicate(at: str) -> str:
    try:
        predicate = state_predicate.parse(at)
    except state_predicate.PredicateError:
        return ""
    for clause in predicate.clauses:
        if isinstance(clause, state_predicate.Call) and clause.name == "cry":
            for arg_name, op, value in clause.args:
                if arg_name == "species" and op == "==":
                    return str(value)
    return ""


def script_label_from_predicate(at: str) -> str:
    try:
        predicate = state_predicate.parse(at)
    except state_predicate.PredicateError:
        return ""
    for clause in predicate.clauses:
        if (
            isinstance(clause, state_predicate.Comparison)
            and clause.field == "script"
            and clause.op == "=="
        ):
            return str(clause.value)
    return ""


def predicate_without_fields(at: str, fields: set[str]) -> str:
    try:
        predicate = state_predicate.parse(at)
    except state_predicate.PredicateError:
        return ""
    clauses = [
        clause.describe()
        for clause in predicate.clauses
        if not (
            isinstance(clause, state_predicate.Comparison)
            and clause.field in fields
        )
    ]
    return " and ".join(clauses)


def static_cry_decode(species: str, *, root: Path) -> dict[str, Any]:
    errors: list[str] = []
    species_id = species_id_for_name(species)
    if species_id is None:
        errors.append(f"unknown Pokemon species: {species}")
    label = cry_label_for_species(species)
    source = root / "audio" / "cries.asm"
    if not source.exists():
        errors.append("missing audio/cries.asm")
    block = {}
    if source.exists():
        blocks = parse_channel_blocks(source.read_text(encoding="utf-8", errors="replace").splitlines())
        block = next((item for item in blocks if item.get("label") == label), {})
        if not block:
            errors.append(f"cry label not found in audio/cries.asm: {label}")
    channels = [int(str(item.get("channel", "0")).lstrip("$") or "0", 0) for item in block.get("channels", [])]
    if block and int(block.get("expected", 0)) != len(channels):
        errors.append(f"{label} channel_count does not match channel declarations")
    return {
        "kind": "debugger_deity_static_cry_decode",
        "valid": not errors,
        "species": species,
        "species_id": species_id,
        "cry_index": (species_id - 1) if species_id is not None else None,
        "label": label,
        "source_file": display_path(source, root=root),
        "line": int(block.get("line", 0)) if block else 0,
        "expected_channel_count": int(block.get("expected", 0)) if block else 0,
        "channels": channels,
        "channel_labels": [str(item.get("label", "")) for item in block.get("channels", [])],
        "errors": errors,
    }


def static_script_decode(script_label: str, *, root: Path) -> dict[str, Any]:
    errors: list[str] = []
    source = script_source_for_label(script_label, root=root)
    if source is None:
        source = root / "maps" / "ElmsLab.asm"
    if not source.exists():
        errors.append(f"missing script source file: {display_path(source, root=root)}")
    block = {}
    if source.exists():
        blocks = parse_script_blocks(source.read_text(encoding="utf-8", errors="replace").splitlines())
        block = next((item for item in blocks if item.get("label") == script_label), {})
        if not block:
            errors.append(f"script label not found in {display_path(source, root=root)}: {script_label}")
    commands = [
        {
            "command": str(command.get("command", "")),
            "line": int(command.get("line", 0)),
            "args": list(command.get("args", [])),
        }
        for command in block.get("commands", [])
    ]
    return {
        "kind": "debugger_deity_static_script_decode",
        "valid": not errors,
        "label": script_label,
        "source_file": display_path(source, root=root),
        "line": int(block.get("line", 0)) if block else 0,
        "command_count": len(commands),
        "commands": commands[:80],
        "errors": errors,
    }


def script_source_for_label(script_label: str, *, root: Path) -> Path | None:
    for path in (root / "maps").glob("*.asm"):
        text = path.read_text(encoding="utf-8", errors="replace")
        if f"{script_label}:" in text:
            return path
    return None


def species_id_for_name(species: str) -> int | None:
    names = parse_pokemon_names()
    wanted = species.upper()
    for species_id, name in names.items():
        if name == wanted:
            return int(species_id)
    return None


def cry_label_for_species(species: str) -> str:
    return "Cry_" + "".join(part.capitalize() for part in species.lower().split("_"))


APU_REGISTERS = {
    "rNR10": 0xFF10,
    "rNR11": 0xFF11,
    "rNR12": 0xFF12,
    "rNR13": 0xFF13,
    "rNR14": 0xFF14,
    "rNR21": 0xFF16,
    "rNR22": 0xFF17,
    "rNR23": 0xFF18,
    "rNR24": 0xFF19,
    "rNR30": 0xFF1A,
    "rNR31": 0xFF1B,
    "rNR32": 0xFF1C,
    "rNR33": 0xFF1D,
    "rNR34": 0xFF1E,
    "rNR41": 0xFF20,
    "rNR42": 0xFF21,
    "rNR43": 0xFF22,
    "rNR44": 0xFF23,
    "rNR50": 0xFF24,
    "rNR51": 0xFF25,
    "rNR52": 0xFF26,
}


def collect_cry_apu_timeline(
    *,
    state_path: str,
    rom_path: str,
    symbols_path: str,
    species: str,
    frames: int,
    root: Path,
) -> dict[str, Any]:
    state = resolve_path(state_path, root=root)
    rom = resolve_path(rom_path, root=root)
    sym = resolve_path(symbols_path, root=root)
    errors: list[str] = []
    if not state.exists():
        errors.append(f"missing state: {state_path}")
    if not rom.exists():
        errors.append(f"missing ROM: {rom_path}")
    if not sym.exists():
        errors.append(f"missing symbols: {symbols_path}")
    species_id = species_id_for_name(species)
    if species_id is None:
        errors.append(f"unknown Pokemon species: {species}")
    symbols = rt.parse_symbols(sym) if sym.exists() else {}
    if "PlayCry" not in symbols:
        errors.append(f"symbol PlayCry missing from {symbols_path}")
    if errors:
        return {"kind": "debugger_deity_cry_apu_timeline", "valid": False, "errors": errors}

    PyBoy = rt.load_pyboy("PyBoy required for deity audio replay")
    try:
        pyboy = PyBoy(str(rom), window="null", sound_emulated=True, log_level="ERROR")
    except TypeError:
        pyboy = PyBoy(str(rom), window="null", sound=True, log_level="ERROR")
    rt.disable_realtime(pyboy)
    rows: list[dict[str, Any]] = []
    try:
        with state.open("rb") as handle:
            pyboy.load_state(handle)
        register_file = pyboy.register_file
        register_file.D = 0
        register_file.E = int(species_id) - 1
        register_file.PC = int(symbols["PlayCry"].address)
        for frame in range(max(1, frames)):
            registers = {name: read_absolute_byte(pyboy, address) for name, address in APU_REGISTERS.items()}
            if frame < 16 or frame % 4 == 0:
                rows.append({"frame": frame, "pc": current_pc(pyboy), "apu": registers})
            try:
                pyboy.tick(1, False, True)
            except TypeError:
                pyboy.tick(1, False)
    finally:
        pyboy.stop()
    payload = json.dumps(rows, sort_keys=True).encode("utf-8")
    return {
        "kind": "debugger_deity_cry_apu_timeline",
        "valid": True,
        "species": species,
        "species_id": species_id,
        "cry_index": int(species_id) - 1,
        "entry_symbol": "PlayCry",
        "frame_count": max(1, frames),
        "sample_count": len(rows),
        "timeline_digest": sha256_bytes(payload),
        "changed_register_count": apu_changed_register_count(rows),
        "first_sample": rows[0] if rows else {},
        "last_sample": rows[-1] if rows else {},
        "errors": [],
    }


def collect_script_vm_stream(
    *,
    state_path: str,
    rom_path: str,
    symbols_path: str,
    script_label: str,
    frames: int,
    root: Path,
) -> dict[str, Any]:
    state = resolve_path(state_path, root=root)
    rom = resolve_path(rom_path, root=root)
    sym = resolve_path(symbols_path, root=root)
    errors: list[str] = []
    if not state.exists():
        errors.append(f"missing state: {state_path}")
    if not rom.exists():
        errors.append(f"missing ROM: {rom_path}")
    if not sym.exists():
        errors.append(f"missing symbols: {symbols_path}")
    symbol_table = parse_symbol_table(sym) if sym.exists() else {}
    rt_symbols = rt.parse_symbols(sym) if sym.exists() else {}
    script_symbol = symbol_table.get(script_label)
    if script_symbol is None:
        errors.append(f"script label not found in {symbols_path}: {script_label}")
    for symbol_name in ("wScriptBank", "wScriptPos", "wScriptRunning", "wScriptMode", "wScriptStackSize"):
        if symbol_name not in symbol_table:
            errors.append(f"symbol {symbol_name} missing from {symbols_path}")
    if errors:
        return {"kind": "debugger_deity_script_vm_stream", "valid": False, "errors": errors}

    PyBoy = rt.load_pyboy("PyBoy required for deity script replay")
    pyboy = PyBoy(str(rom), window="null", sound=False, log_level="ERROR")
    rt.disable_realtime(pyboy)
    rows: list[dict[str, Any]] = []
    try:
        with state.open("rb") as handle:
            pyboy.load_state(handle)
        catalog = load_map_catalog(root=root, labels={})
        trainer_names = parse_trainer_class_names()
        species_names = parse_pokemon_names()
        script_bank = int(script_symbol["bank"])
        script_address = int(script_symbol["address"])
        write_symbol_byte(pyboy, symbol_table, "wScriptBank", script_bank)
        write_symbol_byte(pyboy, symbol_table, "wScriptPos", script_address & 0xFF)
        write_symbol_byte(pyboy, symbol_table, "wScriptPos", (script_address >> 8) & 0xFF, address_offset=1)
        write_symbol_byte(pyboy, symbol_table, "wScriptRunning", 0xFF)
        write_symbol_byte(pyboy, symbol_table, "wScriptMode", 0x01)
        write_symbol_byte(pyboy, symbol_table, "wScriptStackSize", 0)
        last_key = None
        for frame in range(max(1, frames)):
            row = script_vm_row(
                pyboy,
                symbol_table,
                rt_symbols=rt_symbols,
                catalog=catalog,
                trainer_names=trainer_names,
                species_names=species_names,
                frame=frame,
            )
            key = (
                row.get("script_bank"),
                row.get("script_pos"),
                row.get("script_mode"),
                row.get("script_running"),
                row.get("pc"),
            )
            if frame < 16 or key != last_key or frame % 8 == 0:
                rows.append(row)
            last_key = key
            pyboy.tick(1, False)
    finally:
        pyboy.stop()
    payload = json.dumps(rows, sort_keys=True).encode("utf-8")
    return {
        "kind": "debugger_deity_script_vm_stream",
        "valid": True,
        "script_label": script_label,
        "script_bank": int(script_symbol["bank"]),
        "script_address": int(script_symbol["address"]),
        "frame_count": max(1, frames),
        "sample_count": len(rows),
        "stream_digest": sha256_bytes(payload),
        "distinct_script_pos_count": len({row.get("script_pos") for row in rows}),
        "first_sample": rows[0] if rows else {},
        "last_sample": rows[-1] if rows else {},
        "errors": [],
    }


def audio_replay_diff(*, static_cry: dict[str, Any], runtime: dict[str, Any] | None) -> dict[str, Any]:
    runtime = runtime or {}
    valid = bool(
        static_cry.get("valid")
        and runtime.get("valid")
        and static_cry.get("channels")
        and int(runtime.get("sample_count", 0)) > 0
    )
    return {
        "kind": "debugger_deity_audio_replay_diff",
        "valid": valid,
        "static_channels": list(static_cry.get("channels", [])),
        "runtime_changed_register_count": int(runtime.get("changed_register_count", 0) or 0),
        "runtime_digest": runtime.get("timeline_digest", ""),
        "status": "matched_runtime_capture" if valid else "missing_static_or_runtime_audio_capture",
    }


def graphics_replay_diff(*, snapshot: dict[str, Any] | None, at: str, root: Path) -> dict[str, Any]:
    snapshot = snapshot or {}
    surfaces = {surface.get("name"): surface for surface in snapshot.get("surfaces", []) if isinstance(surface, dict)}
    map_source = source_file_for_map_predicate(at, root=root)
    valid = bool(
        snapshot.get("valid")
        and int(snapshot.get("screen_frame_count", 0) or 0) >= 1
        and surfaces.get("VRAM0")
        and surfaces.get("OAM")
    )
    return {
        "kind": "debugger_deity_graphics_replay_diff",
        "valid": valid,
        "map_source": display_path(map_source, root=root) if map_source else "",
        "framebuffer": (snapshot.get("screen_frame") or {}).get("framebuffer", ""),
        "vram0_sha256": (surfaces.get("VRAM0") or {}).get("sha256", ""),
        "vram1_sha256": (surfaces.get("VRAM1") or {}).get("sha256", ""),
        "oam_sha256": (surfaces.get("OAM") or {}).get("sha256", ""),
        "lcd_state": snapshot.get("lcd_state", {}),
        "status": "captured_framebuffer_vram_oam" if valid else "missing_visual_surface_capture",
    }


def script_replay_diff(*, static_script: dict[str, Any], runtime: dict[str, Any] | None) -> dict[str, Any]:
    runtime = runtime or {}
    valid = bool(
        static_script.get("valid")
        and runtime.get("valid")
        and int(static_script.get("command_count", 0) or 0) > 0
        and int(runtime.get("sample_count", 0) or 0) > 0
    )
    return {
        "kind": "debugger_deity_script_replay_diff",
        "valid": valid,
        "static_command_count": int(static_script.get("command_count", 0) or 0),
        "runtime_distinct_script_pos_count": int(runtime.get("distinct_script_pos_count", 0) or 0),
        "runtime_digest": runtime.get("stream_digest", ""),
        "status": "captured_script_vm_stream" if valid else "missing_static_or_runtime_script_capture",
    }


def source_file_for_map_predicate(at: str, *, root: Path) -> Path | None:
    try:
        predicate = state_predicate.parse(at)
    except state_predicate.PredicateError:
        return None
    for clause in predicate.clauses:
        if (
            isinstance(clause, state_predicate.Comparison)
            and clause.field == "map"
            and clause.op == "=="
        ):
            raw = str(clause.value).lower()
            candidate = "".join(part.capitalize() for part in raw.split("_"))
            path = root / "maps" / f"{candidate}.asm"
            return path if path.exists() else None
    return None


def apu_changed_register_count(rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    first = rows[0].get("apu", {})
    changed = set()
    for row in rows[1:]:
        apu = row.get("apu", {})
        for name, value in apu.items():
            if first.get(name) != value:
                changed.add(name)
    return len(changed)


def script_vm_row(
    pyboy: Any,
    symbol_table: dict[str, dict[str, Any]],
    *,
    rt_symbols: dict[str, Any],
    catalog: dict[str, Any],
    trainer_names: dict[int, str],
    species_names: dict[int, str],
    frame: int,
) -> dict[str, Any]:
    script_pos = read_symbol_byte(pyboy, symbol_table, "wScriptPos") | (
        read_symbol_byte(pyboy, symbol_table, "wScriptPos", address_offset=1) << 8
    )
    observed = {}
    try:
        observed = observe(
            pyboy,
            rt_symbols,
            catalog,
            trainer_class_names=trainer_names,
            species_names=species_names,
        )
    except Exception:
        observed = {}
    return {
        "frame": frame,
        "pc": current_pc(pyboy),
        "script_bank": read_symbol_byte(pyboy, symbol_table, "wScriptBank"),
        "script_pos": script_pos,
        "script_mode": read_symbol_byte(pyboy, symbol_table, "wScriptMode"),
        "script_running": read_symbol_byte(pyboy, symbol_table, "wScriptRunning"),
        "script_stack_size": read_symbol_byte(pyboy, symbol_table, "wScriptStackSize"),
        "state": describe_state(observed) if observed else "",
    }


def write_symbol_byte(
    pyboy: Any,
    symbol_table: dict[str, dict[str, Any]],
    symbol: str,
    value: int,
    *,
    address_offset: int = 0,
) -> None:
    entry = symbol_table[symbol]
    write_memory_byte(
        pyboy,
        bank=int(entry.get("bank", 0)),
        address=int(entry.get("address", 0)) + int(address_offset),
        value=value,
    )


def read_symbol_byte(
    pyboy: Any,
    symbol_table: dict[str, dict[str, Any]],
    symbol: str,
    *,
    address_offset: int = 0,
) -> int:
    entry = symbol_table[symbol]
    return read_memory_byte(
        pyboy,
        bank=int(entry.get("bank", 0)),
        address=int(entry.get("address", 0)) + int(address_offset),
    )


def write_memory_byte(pyboy: Any, *, bank: int, address: int, value: int) -> None:
    if 0xD000 <= address <= 0xDFFF and bank:
        try:
            pyboy.memory[bank, address] = value & 0xFF
            return
        except Exception:
            old_bank = int(pyboy.memory[0xFF70])
            pyboy.memory[0xFF70] = bank
            try:
                pyboy.memory[address] = value & 0xFF
            finally:
                pyboy.memory[0xFF70] = old_bank
            return
    pyboy.memory[address] = value & 0xFF


def read_memory_byte(pyboy: Any, *, bank: int, address: int) -> int:
    if 0xD000 <= address <= 0xDFFF and bank:
        try:
            return int(pyboy.memory[bank, address]) & 0xFF
        except Exception:
            old_bank = int(pyboy.memory[0xFF70])
            pyboy.memory[0xFF70] = bank
            try:
                return int(pyboy.memory[address]) & 0xFF
            finally:
                pyboy.memory[0xFF70] = old_bank
    return int(pyboy.memory[address]) & 0xFF


def read_absolute_byte(pyboy: Any, address: int) -> int:
    return int(pyboy.memory[address]) & 0xFF


def run_navigation(
    at: str,
    *,
    rom_path: str,
    symbols_path: str,
    navigator: Navigator,
) -> dict[str, Any]:
    try:
        result = navigator(at, rom=Path(rom_path), symbols_path=Path(symbols_path))
    except Exception as exc:
        return {
            "reached": False,
            "predicate": at,
            "errors": [f"navigation failed: {exc}"],
        }
    result.setdefault("errors", [])
    if not result.get("reached"):
        unmet = ", ".join(result.get("unmet", []))
        result["errors"] = [f"could not reach {at!r}: {unmet or result.get('nearest', 'no state observed')}"]
    return result


def collect_runtime_digest(
    *,
    state_path: str,
    rom_path: str,
    symbols_path: str,
    frames: int,
    root: Path,
) -> dict[str, Any]:
    stream = collect_runtime_stream(
        state_path=state_path,
        rom_path=rom_path,
        symbols_path=symbols_path,
        frames=max(1, frames),
        root=root,
    )
    if stream.get("errors"):
        return stream
    payload = json.dumps(stream.get("frames", []), sort_keys=True).encode("utf-8")
    return {
        "kind": "debugger_deity_runtime_digest",
        "frame_count": stream.get("frame_count", 0),
        "state_digest": sha256_bytes(payload),
        "first_frame": stream.get("frames", [{}])[0] if stream.get("frames") else {},
        "last_frame": stream.get("frames", [{}])[-1] if stream.get("frames") else {},
        "errors": [],
    }


def collect_runtime_stream(
    *,
    state_path: str,
    rom_path: str,
    symbols_path: str,
    frames: int,
    root: Path,
) -> dict[str, Any]:
    state = resolve_path(state_path, root=root)
    rom = resolve_path(rom_path, root=root)
    sym = resolve_path(symbols_path, root=root)
    errors: list[str] = []
    if not state.exists():
        errors.append(f"missing state: {state_path}")
    if not rom.exists():
        errors.append(f"missing ROM: {rom_path}")
    if not sym.exists():
        errors.append(f"missing symbols: {symbols_path}")
    if errors:
        return {"kind": "debugger_deity_runtime_stream", "errors": errors, "frames": []}

    symbols = rt.parse_symbols(sym)
    catalog = load_map_catalog(root=root, labels={})
    trainer_names = parse_trainer_class_names()
    species_names = parse_pokemon_names()
    frame_rows: list[dict[str, Any]] = []
    PyBoy = rt.load_pyboy("PyBoy required for deity runtime stream")
    pyboy = PyBoy(str(rom), window="null", sound=False, log_level="ERROR")
    rt.disable_realtime(pyboy)
    try:
        with state.open("rb") as handle:
            pyboy.load_state(handle)
        for frame in range(max(0, frames)):
            observed = observe(
                pyboy,
                symbols,
                catalog,
                trainer_class_names=trainer_names,
                species_names=species_names,
            )
            frame_rows.append(
                {
                    "frame": frame,
                    "state": describe_state(observed),
                    "observed": observed,
                    "pc": current_pc(pyboy),
                }
            )
            pyboy.tick(1, False)
    finally:
        pyboy.stop()
    return {
        "kind": "debugger_deity_runtime_stream",
        "backend": "pyboy",
        "rom": display_path(rom, root=root),
        "symbols": display_path(sym, root=root),
        "state": display_path(state, root=root),
        "frame_count": len(frame_rows),
        "frames": frame_rows,
        "errors": [],
    }


def current_pc(pyboy: Any) -> int | None:
    try:
        return int(pyboy.register_file.PC)
    except Exception:
        return None


def format_auto_taint(report: dict[str, Any]) -> str:
    lines = [
        "Deity auto-taint",
        f"valid={str(report.get('valid')).lower()} status={report.get('proof_status', '')}",
        f"target={report.get('byte', '')} at={report.get('at', '')}",
    ]
    if report.get("valid"):
        lines.append("taint chain:")
        for step in report.get("taint_chain", []):
            lines.append(f"  - {step.get('kind')}: {step}")
    else:
        lines.extend(f"error: {err}" for err in report.get("errors", []))
    return "\n".join(lines)


def format_surface_replay(report: dict[str, Any]) -> str:
    lines = [
        "Deity surface replay",
        f"valid={str(report.get('valid')).lower()} status={report.get('proof_status', '')}",
        f"surface={report.get('surface', '')} at={report.get('at', '')}",
    ]
    if report.get("valid"):
        diff = report.get("replay_diff") or {}
        runtime = report.get("runtime_replay") or {}
        digest = (
            diff.get("runtime_digest")
            or runtime.get("state_digest")
            or runtime.get("timeline_digest")
            or runtime.get("stream_digest")
            or (runtime.get("screen_frame") or {}).get("framebuffer", "")
        )
        lines.append(f"replay diff: runtime_digest={digest}")
    else:
        lines.extend(f"error: {err}" for err in report.get("errors", []))
    return "\n".join(lines)


def format_live_view(report: dict[str, Any]) -> str:
    lines = [
        "Deity live view",
        f"valid={str(report.get('valid')).lower()} status={report.get('proof_status', '')}",
        f"at={report.get('at', '')} frames={report.get('frames', 0)}",
    ]
    if report.get("valid"):
        stream = report.get("stream") or {}
        lines.append(f"per-frame state: {stream.get('frame_count', 0)} frames")
        if report.get("snapshot"):
            lines.append(f"snapshot={report['snapshot']}")
    else:
        lines.extend(f"error: {err}" for err in report.get("errors", []))
    return "\n".join(lines)


def run_auto_taint_self_test() -> dict[str, Any]:
    target = resolve_byte_target("wCurDamage", symbols_path="pokegold.sym")
    fake_nav = {
        "reached": True,
        "checkpoint": "synthetic",
        "state_path": ".local/tmp/synthetic.state",
        "manifest_path": ".local/tmp/synthetic.manifest.json",
        "map_desc": "synthetic battle state",
    }
    chain = build_taint_chain(target=target, navigation=fake_nav, static_taint={"paths": [{"routine": "DamageCalc"}]})
    return {
        "passed": bool(target.get("valid") and chain and chain[0]["kind"] == "auto_navigation"),
        "detail": f"resolved {target.get('symbol')} at {target.get('address_hex')} with {len(chain)} chain steps",
    }


def run_surface_replay_self_test() -> dict[str, Any]:
    report = build_auto_replay_report(
        surface="graphics",
        at="map=PLAYERS_HOUSE_2F",
        navigator=lambda *_args, **_kwargs: {
            "reached": False,
            "predicate": "map=PLAYERS_HOUSE_2F",
            "unmet": ["synthetic"],
        },
    )
    formatted = format_surface_replay(
        {
            **report,
            "valid": True,
            "replay_diff": {"runtime_digest": "synthetic"},
            "runtime_replay": {"state_digest": "synthetic"},
        }
    )
    return {
        "passed": report["proof_status"].startswith("blocked_by_") and "replay diff" in formatted,
        "detail": "surface replay report fails closed and formatter emits replay diff on valid packets",
    }


def run_live_view_self_test() -> dict[str, Any]:
    formatted = format_live_view(
        {
            "valid": True,
            "proof_status": "live_stream_started",
            "at": "synthetic",
            "frames": 2,
            "stream": {"frame_count": 2},
        }
    )
    return {
        "passed": "per-frame state" in formatted,
        "detail": "live-view headless formatter emits per-frame state marker",
    }
