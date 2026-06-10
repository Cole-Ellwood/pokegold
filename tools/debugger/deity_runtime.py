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
from .runtime_event import runtime_event_envelope
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
    if surface == "content":
        return build_script_map_content_runtime_replay_report(
            at=at,
            rom_path=rom_path,
            symbols_path=symbols_path,
            frames=frames,
            root=root,
        )
    if surface == "dma":
        return build_dma_oam_vram_replay_report(
            at=at,
            rom_path=rom_path,
            symbols_path=symbols_path,
            frames=frames,
            root=root,
        )
    if surface == "interrupts":
        return build_interrupt_entry_exit_replay_report(
            at=at,
            rom_path=rom_path,
            symbols_path=symbols_path,
            frames=frames,
            root=root,
        )
    if surface == "mbc":
        return build_mbc_runtime_transition_replay_report(
            at=at,
            rom_path=rom_path,
            symbols_path=symbols_path,
            frames=frames,
            root=root,
        )
    if surface == "rtc":
        return build_rtc_register_edge_replay_report(
            at=at,
            rom_path=rom_path,
            symbols_path=symbols_path,
            frames=frames,
            root=root,
        )
    if surface == "timer_lcd":
        return build_timer_lcd_mode_replay_report(
            at=at,
            rom_path=rom_path,
            symbols_path=symbols_path,
            frames=frames,
            root=root,
        )
    if surface == "serial":
        return build_serial_transfer_replay_report(
            at=at,
            rom_path=rom_path,
            symbols_path=symbols_path,
            frames=frames,
            root=root,
        )

    navigation = run_navigation(at, rom_path=rom_path, symbols_path=symbols_path, navigator=navigator)
    errors = [*navigation.get("errors", [])]
    if surface not in {"audio", "graphics", "script", "content", "dma", "interrupts", "mbc", "rtc", "timer_lcd", "serial"}:
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


def build_dma_oam_vram_replay_report(
    *,
    at: str,
    rom_path: str,
    symbols_path: str,
    frames: int,
    root: Path,
) -> dict[str, Any]:
    runtime = collect_dma_oam_vram_runtime_stream(
        rom_path=rom_path,
        symbols_path=symbols_path,
        frames=frames,
        root=root,
    )
    errors = list(runtime.get("errors", []))
    valid = not errors and bool(runtime.get("valid"))
    return {
        "schema_version": 1,
        "kind": "debugger_deity_surface_replay",
        "root": str(root),
        "valid": valid,
        "proof_status": "replay_diff_captured" if valid else "blocked_by_dma_replay",
        "evidence_marker": "runtime hardware event stream",
        "surface": "dma",
        "at": at,
        "runtime_replay": runtime,
        "error_count": len(errors),
        "errors": errors,
        "known_limits": [
            "This is PyBoy emulator evidence for selected OAM DMA and general-mode CGB VRAM DMA copies.",
            "HBlank DMA, LCD mode timing restrictions, cross-backend parity, and hardware-cycle proof remain open.",
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
    runtime_events = apu_register_timeline_events(
        rows,
        species=species,
        source_report="debugger_deity_cry_apu_timeline",
    )
    payload = json.dumps(
        {"rows": rows, "runtime_events": runtime_events},
        sort_keys=True,
    ).encode("utf-8")
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
        "runtime_event_count": len(runtime_events),
        "runtime_events": runtime_events,
        "hardware_runtime_event": bool(runtime_events),
        "hardware_runtime_event_source_fields": ["runtime_events"] if runtime_events else [],
        "first_sample": rows[0] if rows else {},
        "last_sample": rows[-1] if rows else {},
        "errors": [],
    }


def build_mbc_runtime_transition_replay_report(
    *,
    at: str,
    rom_path: str,
    symbols_path: str,
    frames: int,
    root: Path,
) -> dict[str, Any]:
    runtime = collect_mbc_runtime_transition_stream(
        rom_path=rom_path,
        symbols_path=symbols_path,
        frames=frames,
        root=root,
    )
    errors = list(runtime.get("errors", []))
    valid = not errors and bool(runtime.get("valid"))
    return {
        "schema_version": 1,
        "kind": "debugger_deity_surface_replay",
        "root": str(root),
        "valid": valid,
        "proof_status": "replay_diff_captured" if valid else "blocked_by_mbc_replay",
        "evidence_marker": "runtime MBC transition event stream",
        "surface": "mbc",
        "at": at,
        "runtime_replay": runtime,
        "error_count": len(errors),
        "errors": errors,
        "known_limits": [
            "This is PyBoy emulator evidence for selected MBC3 ROM, SRAM, and RTC select/latch transitions.",
            "It does not claim RTC halt, carry, day-overflow, RTC register-write, or cross-backend correctness.",
        ],
    }


def build_rtc_register_edge_replay_report(
    *,
    at: str,
    rom_path: str,
    symbols_path: str,
    frames: int,
    root: Path,
) -> dict[str, Any]:
    runtime = collect_rtc_register_edge_runtime_stream(
        rom_path=rom_path,
        symbols_path=symbols_path,
        frames=frames,
        root=root,
    )
    errors = list(runtime.get("errors", []))
    valid = not errors and bool(runtime.get("valid"))
    return {
        "schema_version": 1,
        "kind": "debugger_deity_surface_replay",
        "root": str(root),
        "valid": valid,
        "proof_status": "replay_diff_captured" if valid else "blocked_by_rtc_replay",
        "evidence_marker": "runtime RTC register edge replay",
        "surface": "rtc",
        "at": at,
        "runtime_replay": runtime,
        "error_count": len(errors),
        "errors": errors,
        "known_limits": [
            "This is PyBoy emulator evidence for MBC3 RTC carry-bit write/readback and seeded day-overflow readback.",
            "Seeded day-overflow cases prove register readback from an RTC file basis, not naturally elapsed 512-day runtime.",
            "PyBoy RTC halt-bit readback is observed, but halt semantics remain unimplemented and unproven.",
            "It does not claim cross-backend or hardware RTC parity.",
        ],
    }


def build_interrupt_entry_exit_replay_report(
    *,
    at: str,
    rom_path: str,
    symbols_path: str,
    frames: int,
    root: Path,
) -> dict[str, Any]:
    runtime = collect_interrupt_entry_exit_runtime_stream(
        rom_path=rom_path,
        symbols_path=symbols_path,
        frames=frames,
        root=root,
    )
    errors = list(runtime.get("errors", []))
    valid = not errors and bool(runtime.get("valid"))
    return {
        "schema_version": 1,
        "kind": "debugger_deity_surface_replay",
        "root": str(root),
        "valid": valid,
        "proof_status": "replay_diff_captured" if valid else "blocked_by_interrupt_replay",
        "evidence_marker": "runtime interrupt entry/exit event stream",
        "surface": "interrupts",
        "at": at,
        "runtime_replay": runtime,
        "error_count": len(errors),
        "errors": errors,
        "known_limits": [
            "This is PyBoy emulator evidence for VBlank, LCD STAT, timer, serial, and joypad interrupt entry/exit pairs.",
            "It does not claim serial transfer behavior, cycle-exact IME timing, or LCD mode/timer overflow event streams.",
        ],
    }


def build_timer_lcd_mode_replay_report(
    *,
    at: str,
    rom_path: str,
    symbols_path: str,
    frames: int,
    root: Path,
) -> dict[str, Any]:
    runtime = collect_timer_lcd_mode_runtime_stream(
        rom_path=rom_path,
        symbols_path=symbols_path,
        frames=frames,
        root=root,
    )
    errors = list(runtime.get("errors", []))
    valid = not errors and bool(runtime.get("valid"))
    return {
        "schema_version": 1,
        "kind": "debugger_deity_surface_replay",
        "root": str(root),
        "valid": valid,
        "proof_status": "replay_diff_captured" if valid else "blocked_by_timer_lcd_replay",
        "evidence_marker": "runtime timer/LCD hardware event stream",
        "surface": "timer_lcd",
        "at": at,
        "runtime_replay": runtime,
        "error_count": len(errors),
        "errors": errors,
        "known_limits": [
            "This is PyBoy emulator evidence from controlled CPU polling loops over selected timer and LCD registers.",
            "It is not cycle-exact hardware parity and does not claim cross-backend LCD/timer correctness.",
        ],
    }


def build_serial_transfer_replay_report(
    *,
    at: str,
    rom_path: str,
    symbols_path: str,
    frames: int,
    root: Path,
) -> dict[str, Any]:
    runtime = collect_serial_transfer_runtime_stream(
        rom_path=rom_path,
        symbols_path=symbols_path,
        frames=frames,
        root=root,
    )
    errors = list(runtime.get("errors", []))
    valid = not errors and bool(runtime.get("valid"))
    return {
        "schema_version": 1,
        "kind": "debugger_deity_surface_replay",
        "root": str(root),
        "valid": valid,
        "proof_status": "replay_diff_captured" if valid else "blocked_by_serial_replay",
        "evidence_marker": "runtime serial transfer event stream",
        "surface": "serial",
        "at": at,
        "runtime_replay": runtime,
        "error_count": len(errors),
        "errors": errors,
        "known_limits": [
            "This is PyBoy emulator evidence for controlled internal-clock SB/SC transfers.",
            "It does not claim a linked peer, cable timing, Mystery Gift protocol completion, or cross-backend serial parity.",
        ],
    }


def build_script_map_content_runtime_replay_report(
    *,
    at: str,
    rom_path: str,
    symbols_path: str,
    frames: int,
    root: Path,
) -> dict[str, Any]:
    runtime = collect_script_map_content_runtime_replays(
        rom_path=rom_path,
        symbols_path=symbols_path,
        frames=frames,
        root=root,
    )
    errors = list(runtime.get("errors", []))
    valid = not errors and bool(runtime.get("valid"))
    return {
        "schema_version": 1,
        "kind": "debugger_deity_surface_replay",
        "root": str(root),
        "valid": valid,
        "proof_status": "replay_diff_captured" if valid else "blocked_by_content_runtime_replay",
        "evidence_marker": "runtime script/map content helper replay",
        "surface": "content",
        "at": at,
        "runtime_replay": runtime,
        "error_count": len(errors),
        "errors": errors,
        "known_limits": [
            "This is a direct PyBoy helper harness for selected Azalea warp/object content scenarios.",
            "It proves selected ROM helper behavior after synthesized WRAM setup, not full overworld button/input flow coverage.",
        ],
    }


def collect_dma_oam_vram_runtime_stream(
    *,
    rom_path: str,
    symbols_path: str,
    frames: int,
    root: Path,
) -> dict[str, Any]:
    rom = resolve_path(rom_path or str(DEFAULT_ROM), root=root)
    sym = resolve_path(symbols_path or str(DEFAULT_SYMBOLS), root=root)
    errors: list[str] = []
    if not rom.exists():
        errors.append(f"missing ROM: {rom_path}")
    if symbols_path and not sym.exists():
        errors.append(f"missing symbols: {symbols_path}")
    if errors:
        return {"kind": "debugger_deity_dma_oam_vram_runtime_event_stream", "valid": False, "errors": errors}

    PyBoy = rt.load_pyboy("PyBoy required for DMA runtime replay")
    pyboy = PyBoy(str(rom), window="null", sound=False, log_level="ERROR")
    rt.disable_realtime(pyboy)
    try:
        oam_case = run_oam_dma_runtime_case(pyboy, frames=max(1, frames))
        vram_case = run_vram_dma_runtime_case(pyboy, frames=max(1, frames))
    finally:
        try:
            pyboy.stop(save=False)
        except TypeError:
            pyboy.stop()
    cases = [oam_case, vram_case]
    runtime_events = dma_runtime_events(cases)
    valid = all(case.get("exact_match") is True for case in cases) and len(runtime_events) == len(cases)
    payload = json.dumps({"cases": cases, "runtime_events": runtime_events}, sort_keys=True).encode("utf-8")
    return {
        "kind": "debugger_deity_dma_oam_vram_runtime_event_stream",
        "schema_version": 1,
        "valid": valid,
        "backend": "pyboy",
        "rom_path": display_path(rom, root=root),
        "symbols_path": display_path(sym, root=root) if sym.exists() else "",
        "frame_count": max(1, frames),
        "case_count": len(cases),
        "runtime_event_count": len(runtime_events),
        "stream_digest": sha256_bytes(payload),
        "cases": cases,
        "runtime_events": runtime_events,
        "errors": [] if valid else ["DMA runtime byte validation failed"],
        "known_limits": [
            "OAM DMA is triggered by an executed HRAM ldh [$46],a write.",
            "VRAM DMA covers one selected general-mode 16-byte CGB DMA block.",
            "HBlank DMA and LCD mode timing restrictions are not claimed.",
        ],
    }


def run_oam_dma_runtime_case(pyboy: Any, *, frames: int) -> dict[str, Any]:
    source = 0xC000
    destination = 0xFE00
    byte_count = 0xA0
    expected = [((index * 7) + 3) & 0xFF for index in range(byte_count)]
    for index, value in enumerate(expected):
        pyboy.memory[source + index] = value
    execute_hram_snippet(
        pyboy,
        [
            0x3E,
            (source >> 8) & 0xFF,
            0xE0,
            0x46,
            0x18,
            0xFE,
        ],
        frames=frames,
    )
    observed = [read_absolute_byte(pyboy, destination + index) for index in range(byte_count)]
    match_count = sum(1 for left, right in zip(expected, observed) if left == right)
    return {
        "case_id": "oam_dma_hram_trigger",
        "dma_kind": "oam_dma",
        "trigger_register": "FF46",
        "trigger_value": (source >> 8) & 0xFF,
        "source_range": f"${source:04X}-${source + byte_count - 1:04X}",
        "destination_range": f"${destination:04X}-${destination + byte_count - 1:04X}",
        "byte_count": byte_count,
        "match_count": match_count,
        "exact_match": match_count == byte_count,
        "source_sample": expected[:16],
        "destination_sample": observed[:16],
        "pc_after": current_pc(pyboy),
    }


def run_vram_dma_runtime_case(pyboy: Any, *, frames: int) -> dict[str, Any]:
    source = 0xC100
    destination = 0x8000
    byte_count = 0x10
    expected = [(0x80 + index) & 0xFF for index in range(byte_count)]
    for index, value in enumerate(expected):
        pyboy.memory[source + index] = value
    execute_hram_snippet(
        pyboy,
        [
            0x3E, (source >> 8) & 0xFF, 0xE0, 0x51,
            0x3E, source & 0xF0, 0xE0, 0x52,
            0x3E, ((destination - 0x8000) >> 8) & 0x1F, 0xE0, 0x53,
            0x3E, destination & 0xF0, 0xE0, 0x54,
            0x3E, 0x00, 0xE0, 0x55,
            0x18, 0xFE,
        ],
        frames=frames,
    )
    observed = [read_absolute_byte(pyboy, destination + index) for index in range(byte_count)]
    match_count = sum(1 for left, right in zip(expected, observed) if left == right)
    return {
        "case_id": "cgb_vram_dma_general_16_bytes",
        "dma_kind": "cgb_vram_dma_general",
        "trigger_register": "FF55",
        "trigger_value": 0,
        "source_range": f"${source:04X}-${source + byte_count - 1:04X}",
        "destination_range": f"${destination:04X}-${destination + byte_count - 1:04X}",
        "byte_count": byte_count,
        "match_count": match_count,
        "exact_match": match_count == byte_count,
        "source_sample": expected[:16],
        "destination_sample": observed[:16],
        "post_ff55": read_absolute_byte(pyboy, 0xFF55),
        "pc_after": current_pc(pyboy),
    }


def execute_hram_snippet(pyboy: Any, opcodes: list[int], *, frames: int) -> None:
    start = 0xFF80
    for index, opcode in enumerate(opcodes):
        pyboy.memory[start + index] = int(opcode) & 0xFF
    pyboy.register_file.PC = start
    pyboy.register_file.SP = 0xDFFF
    for _ in range(max(1, frames)):
        pyboy.tick(1, False)


def dma_runtime_events(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for seq, case in enumerate(cases):
        if case.get("exact_match") is not True:
            continue
        events.append(
            runtime_event_envelope(
                event_kind="hardware_event",
                source_kind="pyboy_dma_runtime",
                source_report="debugger_deity_dma_oam_vram_runtime_event_stream",
                seq=seq,
                proof_status="runtime_observed",
                observation_type="explicit_hardware_event",
                scope={"backend": "pyboy", "surface": "dma", "dma_kind": case.get("dma_kind", "")},
                subjects={
                    "registers": [case.get("trigger_register", "")],
                    "source_range": case.get("source_range", ""),
                    "destination_range": case.get("destination_range", ""),
                },
                precision={
                    "byte_count": case.get("byte_count", 0),
                    "match_count": case.get("match_count", 0),
                    "byte_exact_copy": bool(case.get("exact_match", False)),
                },
                validation={
                    "case_id": case.get("case_id", ""),
                    "trigger_value": case.get("trigger_value", 0),
                },
                payload=case,
            )
        )
    return events


def collect_mbc_runtime_transition_stream(
    *,
    rom_path: str,
    symbols_path: str,
    frames: int,
    root: Path,
) -> dict[str, Any]:
    rom = resolve_path(rom_path or str(DEFAULT_ROM), root=root)
    sym = resolve_path(symbols_path or str(DEFAULT_SYMBOLS), root=root)
    errors: list[str] = []
    if not rom.exists():
        errors.append(f"missing ROM: {rom_path}")
    if symbols_path and not sym.exists():
        errors.append(f"missing symbols: {symbols_path}")
    if errors:
        return {"kind": "debugger_deity_mbc_runtime_transition_replay_corpus", "valid": False, "errors": errors}

    rom_bytes = rom.read_bytes()
    header = mbc3_rom_header_summary(rom_bytes)
    if header["cartridge_type_code"] != 0x10:
        errors.append(f"unexpected cartridge type for Pokemon Gold MBC3 replay: ${header['cartridge_type_code']:02X}")
    PyBoy = rt.load_pyboy("PyBoy required for MBC runtime replay")

    import shutil
    import tempfile

    with tempfile.TemporaryDirectory(prefix="mbc-runtime-") as tmp:
        temp_rom = Path(tmp) / rom.name
        shutil.copyfile(rom, temp_rom)
        pyboy = PyBoy(str(temp_rom), window="null", sound=False, log_level="ERROR")
        rt.disable_realtime(pyboy)
        try:
            rom_bank_case = run_mbc_rom_bank_select_case(
                pyboy,
                rom_bytes=rom_bytes,
                frames=max(1, frames),
            )
            sram_enable_case = run_mbc_sram_enable_disable_case(pyboy, frames=max(1, frames))
            sram_bank_case = run_mbc_sram_bank_select_case(pyboy, frames=max(1, frames))
            rtc_select_case = run_mbc_rtc_register_select_latch_case(pyboy, frames=max(1, frames))
        finally:
            try:
                pyboy.stop(save=False)
            except TypeError:
                pyboy.stop()

    cases = [rom_bank_case, sram_enable_case, sram_bank_case, rtc_select_case]
    runtime_events = mbc_runtime_events(cases)
    valid = (
        not errors
        and all(case.get("transition_observed") is True for case in cases)
        and len(runtime_events) == len(cases)
    )
    payload = json.dumps({"header": header, "cases": cases, "runtime_events": runtime_events}, sort_keys=True).encode("utf-8")
    return {
        "kind": "debugger_deity_mbc_runtime_transition_replay_corpus",
        "schema_version": 1,
        "valid": valid,
        "backend": "pyboy",
        "rom_path": display_path(rom, root=root),
        "symbols_path": display_path(sym, root=root) if sym.exists() else "",
        "frame_count": max(1, frames),
        "rom_header": header,
        "case_count": len(cases),
        "runtime_event_count": len(runtime_events),
        "stream_digest": sha256_bytes(payload),
        "cases": cases,
        "runtime_events": runtime_events,
        "errors": [] if valid else [*errors, "MBC runtime transition validation failed"],
        "known_limits": [
            "ROM bank, SRAM enable, SRAM bank select, and RTC register select/latch cases are selected MBC3 probes.",
            "RTC halt, carry, day-overflow, RTC register-write semantics, and cross-backend parity remain separate open proof gaps.",
        ],
    }


def mbc3_rom_header_summary(rom_bytes: bytes) -> dict[str, Any]:
    return {
        "cartridge_type_code": rom_bytes[0x147] if len(rom_bytes) > 0x147 else -1,
        "rom_size_code": rom_bytes[0x148] if len(rom_bytes) > 0x148 else -1,
        "ram_size_code": rom_bytes[0x149] if len(rom_bytes) > 0x149 else -1,
        "rom_size_bytes": len(rom_bytes),
        "rom_bank_count": len(rom_bytes) // 0x4000,
        "cartridge_type": "MBC3+TIMER+RAM+BATTERY",
    }


def run_mbc_rom_bank_select_case(pyboy: Any, *, rom_bytes: bytes, frames: int) -> dict[str, Any]:
    sample_size = 16
    transitions: list[dict[str, Any]] = []
    for raw_value in (0x00, 0x01, 0x02, 0x03, 0x10, 0x22, 0x7F):
        bank = mbc3_rom_bank_for_value(raw_value)
        expected = list(rom_bytes[bank * 0x4000: bank * 0x4000 + sample_size])
        execute_absolute_write(pyboy, 0x2000, raw_value, frames=frames)
        observed = read_byte_window(pyboy, 0x4000, sample_size)
        transitions.append(
            {
                "write_value": raw_value,
                "expected_bank": bank,
                "window": "$4000-$400F",
                "expected_sample": expected,
                "observed_sample": observed,
                "sample_match": len(expected) == sample_size and observed == expected,
            }
        )
    matched_banks = {
        int(item["expected_bank"])
        for item in transitions
        if item.get("sample_match") is True
    }
    zero_transition = next(item for item in transitions if item["write_value"] == 0)
    return {
        "case_id": "mbc3_rom_bank_select_window",
        "transition_kind": "rom_bank_select",
        "write_range": "$2000-$3FFF",
        "write_address": "$2000",
        "transition_count": len(transitions),
        "matched_bank_count": len(matched_banks),
        "zero_select_maps_to_bank_one": zero_transition.get("expected_bank") == 1 and zero_transition.get("sample_match") is True,
        "transitions": transitions,
        "transition_observed": all(item.get("sample_match") is True for item in transitions),
        "pc_after": current_pc(pyboy),
    }


def run_mbc_sram_enable_disable_case(pyboy: Any, *, frames: int) -> dict[str, Any]:
    marker = 0xA5
    blocked_marker = 0x5A
    execute_absolute_write(pyboy, 0x0000, 0x0A, frames=frames)
    execute_absolute_write(pyboy, 0x4000, 0x00, frames=frames)
    execute_absolute_write(pyboy, 0xA000, marker, frames=frames)
    enabled_read = read_absolute_byte(pyboy, 0xA000)
    execute_absolute_write(pyboy, 0x0000, 0x00, frames=frames)
    disabled_read = read_absolute_byte(pyboy, 0xA000)
    execute_absolute_write(pyboy, 0xA000, blocked_marker, frames=frames)
    disabled_after_write = read_absolute_byte(pyboy, 0xA000)
    execute_absolute_write(pyboy, 0x0000, 0x0A, frames=frames)
    execute_absolute_write(pyboy, 0x4000, 0x00, frames=frames)
    reenabled_read = read_absolute_byte(pyboy, 0xA000)
    return {
        "case_id": "mbc3_sram_enable_disable",
        "transition_kind": "sram_enable_disable",
        "write_range": "$0000-$1FFF",
        "write_address": "$0000",
        "enable_value": 0x0A,
        "disable_value": 0x00,
        "marker": marker,
        "blocked_marker": blocked_marker,
        "enabled_read": enabled_read,
        "disabled_read": disabled_read,
        "disabled_after_write": disabled_after_write,
        "reenabled_read": reenabled_read,
        "enabled_readback_matches": enabled_read == marker,
        "disabled_readback_open_bus": disabled_read == 0xFF,
        "disabled_write_blocked": disabled_after_write == 0xFF,
        "reenabled_preserved": reenabled_read == marker,
        "transition_observed": (
            enabled_read == marker
            and disabled_read == 0xFF
            and disabled_after_write == 0xFF
            and reenabled_read == marker
        ),
        "pc_after": current_pc(pyboy),
    }


def run_mbc_sram_bank_select_case(pyboy: Any, *, frames: int) -> dict[str, Any]:
    bank_markers = {0: 0x11, 1: 0x22, 2: 0x33, 3: 0x44}
    execute_absolute_write(pyboy, 0x0000, 0x0A, frames=frames)
    writes: list[dict[str, Any]] = []
    for bank, marker in bank_markers.items():
        execute_absolute_write(pyboy, 0x4000, bank, frames=frames)
        execute_absolute_write(pyboy, 0xA000, marker, frames=frames)
        writes.append({"sram_bank": bank, "marker": marker})
    reads: list[dict[str, Any]] = []
    for bank, marker in bank_markers.items():
        execute_absolute_write(pyboy, 0x4000, bank, frames=frames)
        observed = read_absolute_byte(pyboy, 0xA000)
        reads.append(
            {
                "sram_bank": bank,
                "expected_marker": marker,
                "observed": observed,
                "match": observed == marker,
            }
        )
    isolated_count = sum(1 for item in reads if item.get("match") is True)
    return {
        "case_id": "mbc3_sram_bank_select_isolation",
        "transition_kind": "sram_bank_select",
        "write_range": "$4000-$5FFF",
        "write_address": "$4000",
        "sram_window": "$A000-$BFFF",
        "writes": writes,
        "reads": reads,
        "isolated_bank_count": isolated_count,
        "transition_observed": isolated_count == len(bank_markers),
        "pc_after": current_pc(pyboy),
    }


def run_mbc_rtc_register_select_latch_case(pyboy: Any, *, frames: int) -> dict[str, Any]:
    import time

    sram_marker = 0xA5
    execute_absolute_write(pyboy, 0x0000, 0x0A, frames=frames)
    execute_absolute_write(pyboy, 0x4000, 0x00, frames=frames)
    execute_absolute_write(pyboy, 0xA000, sram_marker, frames=frames)
    execute_absolute_write(pyboy, 0x6000, 0x00, frames=frames)
    execute_absolute_write(pyboy, 0x6000, 0x01, frames=frames)
    execute_absolute_write(pyboy, 0x4000, 0x08, frames=frames)
    first_seconds = read_absolute_byte(pyboy, 0xA000)
    time.sleep(1.2)
    tick_pyboy(pyboy, max(1, frames))
    stale_seconds = read_absolute_byte(pyboy, 0xA000)
    execute_absolute_write(pyboy, 0x6000, 0x00, frames=frames)
    execute_absolute_write(pyboy, 0x6000, 0x01, frames=frames)
    execute_absolute_write(pyboy, 0x4000, 0x08, frames=frames)
    relatched_seconds = read_absolute_byte(pyboy, 0xA000)
    register_specs = [
        (0x08, "seconds", "0-59"),
        (0x09, "minutes", "0-59"),
        (0x0A, "hours", "0-23"),
        (0x0B, "day_low", "0-255"),
        (0x0C, "day_high", "bitmask 0xC1"),
    ]
    registers: list[dict[str, Any]] = []
    for select_value, name, expected_range in register_specs:
        execute_absolute_write(pyboy, 0x4000, select_value, frames=frames)
        observed = read_absolute_byte(pyboy, 0xA000)
        registers.append(
            {
                "select_value": select_value,
                "name": name,
                "expected_range": expected_range,
                "observed": observed,
                "within_expected_range": mbc3_rtc_register_value_in_range(name, observed),
            }
        )
    execute_absolute_write(pyboy, 0x4000, 0x00, frames=frames)
    sram_read_after_rtc_select = read_absolute_byte(pyboy, 0xA000)
    bounded = all(item.get("within_expected_range") is True for item in registers)
    latch_observed = stale_seconds == first_seconds and relatched_seconds != first_seconds
    sram_marker_restored = sram_read_after_rtc_select == sram_marker
    return {
        "case_id": "mbc3_rtc_register_select_latch",
        "transition_kind": "rtc_register_select_latch",
        "write_range": "$4000-$5FFF,$6000-$7FFF",
        "select_write_address": "$4000",
        "latch_write_address": "$6000",
        "latch_sequence": [0x00, 0x01],
        "first_seconds": first_seconds,
        "stale_seconds_without_relatch": stale_seconds,
        "relatched_seconds": relatched_seconds,
        "latch_sequence_observed": latch_observed,
        "registers": registers,
        "rtc_register_count": len(registers),
        "bounded_register_values": bounded,
        "sram_marker": sram_marker,
        "sram_read_after_rtc_select": sram_read_after_rtc_select,
        "sram_marker_restored": sram_marker_restored,
        "transition_observed": bounded and latch_observed and sram_marker_restored,
        "known_limits": [
            "This case observes RTC register select and latch readback only.",
            "It does not claim RTC halt, carry, day-overflow, or RTC register-write correctness.",
        ],
        "pc_after": current_pc(pyboy),
    }


def mbc3_rom_bank_for_value(value: int) -> int:
    bank = int(value) & 0x7F
    return bank if bank else 1


def mbc3_rtc_register_value_in_range(name: str, value: int) -> bool:
    value = int(value) & 0xFF
    if name in {"seconds", "minutes"}:
        return 0 <= value <= 59
    if name == "hours":
        return 0 <= value <= 23
    if name == "day_low":
        return 0 <= value <= 0xFF
    if name == "day_high":
        return (value & ~0xC1) == 0
    return False


def execute_absolute_write(pyboy: Any, address: int, value: int, *, frames: int) -> None:
    execute_hram_snippet(
        pyboy,
        [
            0xF3,
            0x3E,
            int(value) & 0xFF,
            0xEA,
            int(address) & 0xFF,
            (int(address) >> 8) & 0xFF,
            0x18,
            0xFE,
        ],
        frames=frames,
    )


def tick_pyboy(pyboy: Any, frames: int) -> None:
    for _ in range(max(1, frames)):
        pyboy.tick(1, False)


def read_byte_window(pyboy: Any, start: int, count: int) -> list[int]:
    return [read_absolute_byte(pyboy, start + index) for index in range(count)]


def mbc_runtime_events(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for seq, case in enumerate(cases):
        if case.get("transition_observed") is not True:
            continue
        events.append(
            runtime_event_envelope(
                event_kind="hardware_event",
                source_kind="pyboy_mbc_runtime",
                source_report="debugger_deity_mbc_runtime_transition_replay_corpus",
                seq=seq,
                proof_status="runtime_observed",
                observation_type="explicit_hardware_event",
                scope={
                    "backend": "pyboy",
                    "surface": "mbc",
                    "mbc_transition": case.get("transition_kind", ""),
                },
                subjects={
                    "write_range": case.get("write_range", ""),
                    "write_address": case.get("write_address", "")
                    or case.get("select_write_address", ""),
                    "sram_window": case.get("sram_window", ""),
                },
                precision={
                    "transition_observed": bool(case.get("transition_observed", False)),
                    "transition_count": case.get("transition_count", 1),
                    "matched_bank_count": case.get("matched_bank_count", 0),
                    "isolated_bank_count": case.get("isolated_bank_count", 0),
                    "rtc_register_count": case.get("rtc_register_count", 0),
                },
                validation={
                    "case_id": case.get("case_id", ""),
                    "transition_kind": case.get("transition_kind", ""),
                },
                payload=case,
            )
        )
    return events


def collect_rtc_register_edge_runtime_stream(
    *,
    rom_path: str,
    symbols_path: str,
    frames: int,
    root: Path,
) -> dict[str, Any]:
    import shutil
    import tempfile
    import time

    rom = resolve_path(rom_path or str(DEFAULT_ROM), root=root)
    sym = resolve_path(symbols_path or str(DEFAULT_SYMBOLS), root=root)
    errors: list[str] = []
    if not rom.exists():
        errors.append(f"missing ROM: {rom_path}")
    if symbols_path and not sym.exists():
        errors.append(f"missing symbols: {symbols_path}")
    if errors:
        return {"kind": "debugger_deity_rtc_register_edge_runtime_replay", "valid": False, "errors": errors}

    rom_bytes = rom.read_bytes()
    header = mbc3_rom_header_summary(rom_bytes)
    if header["cartridge_type_code"] != 0x10:
        errors.append(f"unexpected cartridge type for Pokemon Gold RTC replay: ${header['cartridge_type_code']:02X}")
    PyBoy = rt.load_pyboy("PyBoy required for RTC register edge replay")

    cases: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="rtc-runtime-") as tmp:
        tmp_path = Path(tmp)
        writable_rom = tmp_path / rom.name
        shutil.copyfile(rom, writable_rom)
        pyboy = PyBoy(str(writable_rom), window="null", sound=False, log_level="ERROR")
        rt.disable_realtime(pyboy)
        try:
            cases.append(run_rtc_day_high_carry_register_write_case(pyboy, frames=max(1, frames)))
            cases.append(run_rtc_halt_bit_nonsemantic_control_case(pyboy, frames=max(1, frames)))
        finally:
            try:
                pyboy.stop(save=False)
            except TypeError:
                pyboy.stop()

        now = time.time()
        for days in (511, 512, 513):
            seeded_rom = tmp_path / f"rtc_days_{days}_{rom.name}"
            shutil.copyfile(rom, seeded_rom)
            seed_rtc_file(seeded_rom, elapsed_days=days, now=now)
            seeded_pyboy = PyBoy(str(seeded_rom), window="null", sound=False, log_level="ERROR")
            rt.disable_realtime(seeded_pyboy)
            try:
                cases.append(
                    run_rtc_seeded_day_counter_case(
                        seeded_pyboy,
                        elapsed_days=days,
                        frames=max(1, frames),
                    )
                )
            finally:
                try:
                    seeded_pyboy.stop(save=False)
                except TypeError:
                    seeded_pyboy.stop()

    runtime_events = rtc_register_edge_runtime_events(cases)
    valid = (
        not errors
        and all(case.get("transition_observed") is True for case in cases)
        and len(runtime_events) == len(cases)
    )
    payload = json.dumps({"header": header, "cases": cases, "runtime_events": runtime_events}, sort_keys=True).encode("utf-8")
    return {
        "kind": "debugger_deity_rtc_register_edge_runtime_replay",
        "schema_version": 1,
        "valid": valid,
        "backend": "pyboy",
        "rom_path": display_path(rom, root=root),
        "symbols_path": display_path(sym, root=root) if sym.exists() else "",
        "frame_count": max(1, frames),
        "rom_header": header,
        "case_count": len(cases),
        "runtime_event_count": len(runtime_events),
        "stream_digest": sha256_bytes(payload),
        "cases": cases,
        "runtime_events": runtime_events,
        "errors": [] if valid else [*errors, "RTC register edge replay validation failed"],
        "known_limits": [
            "Carry-bit write/readback and seeded day-overflow readback are selected PyBoy MBC3 RTC probes.",
            "Seeded day-overflow cases use a prepared .rtc timezero basis, not naturally elapsed 512-day runtime.",
            "PyBoy records the RTC halt bit but does not stop the clock; halt semantics remain open.",
            "Cross-backend and hardware RTC parity remain open.",
        ],
    }


def seed_rtc_file(rom_path: Path, *, elapsed_days: int, now: float) -> None:
    import struct

    elapsed_seconds = int(elapsed_days) * 24 * 60 * 60
    timezero = float(now) - float(elapsed_seconds)
    Path(str(rom_path) + ".rtc").write_bytes(struct.pack("<d", timezero) + bytes([0, 0]))


def run_rtc_day_high_carry_register_write_case(pyboy: Any, *, frames: int) -> dict[str, Any]:
    execute_absolute_write(pyboy, 0x0000, 0x0A, frames=frames)
    execute_absolute_write(pyboy, 0x4000, 0x0C, frames=frames)
    execute_absolute_write(pyboy, 0xA000, 0x80, frames=frames)
    latch_rtc(pyboy, frames=frames)
    carry_set_day_high = read_rtc_register(pyboy, 0x0C, frames=frames)
    execute_absolute_write(pyboy, 0x4000, 0x0C, frames=frames)
    execute_absolute_write(pyboy, 0xA000, 0x00, frames=frames)
    latch_rtc(pyboy, frames=frames)
    carry_clear_day_high = read_rtc_register(pyboy, 0x0C, frames=frames)
    carry_set = (carry_set_day_high & 0x80) == 0x80
    carry_clear = (carry_clear_day_high & 0x80) == 0
    return {
        "case_id": "rtc_day_high_carry_register_write_readback",
        "transition_kind": "rtc_register_write_carry_readback",
        "write_range": "$4000-$5FFF,$6000-$7FFF,$A000-$BFFF",
        "select_write_address": "$4000",
        "latch_write_address": "$6000",
        "rtc_data_window": "$A000-$BFFF",
        "set_write_value": 0x80,
        "clear_write_value": 0x00,
        "carry_set_day_high": carry_set_day_high,
        "carry_clear_day_high": carry_clear_day_high,
        "carry_set_readback": carry_set,
        "carry_clear_readback": carry_clear,
        "halt_semantics_proven": False,
        "transition_observed": carry_set and carry_clear,
        "known_limits": [
            "This case proves RTC day-high carry bit write/readback only.",
            "It does not prove halt semantics or naturally elapsed day overflow.",
        ],
        "pc_after": current_pc(pyboy),
    }


def run_rtc_halt_bit_nonsemantic_control_case(pyboy: Any, *, frames: int) -> dict[str, Any]:
    import time

    execute_absolute_write(pyboy, 0x0000, 0x0A, frames=frames)
    execute_absolute_write(pyboy, 0x4000, 0x0C, frames=frames)
    execute_absolute_write(pyboy, 0xA000, 0x40, frames=frames)
    latch_rtc(pyboy, frames=frames)
    day_high_with_halt = read_rtc_register(pyboy, 0x0C, frames=frames)
    seconds_before = read_rtc_register(pyboy, 0x08, frames=frames)
    time.sleep(1.2)
    tick_pyboy(pyboy, max(1, frames))
    latch_rtc(pyboy, frames=frames)
    seconds_after = read_rtc_register(pyboy, 0x08, frames=frames)
    halt_bit_readback = (day_high_with_halt & 0x40) == 0x40
    seconds_advanced = seconds_after != seconds_before
    return {
        "case_id": "rtc_halt_bit_readback_nonsemantic_control",
        "transition_kind": "rtc_halt_bit_readback_nonsemantic_control",
        "write_range": "$4000-$5FFF,$6000-$7FFF,$A000-$BFFF",
        "select_write_address": "$4000",
        "latch_write_address": "$6000",
        "rtc_data_window": "$A000-$BFFF",
        "halt_write_value": 0x40,
        "day_high_with_halt": day_high_with_halt,
        "seconds_before": seconds_before,
        "seconds_after": seconds_after,
        "halt_bit_readback": halt_bit_readback,
        "seconds_advanced_while_halt_bit_set": seconds_advanced,
        "halt_semantics_proven": False,
        "transition_observed": halt_bit_readback and seconds_advanced,
        "known_limits": [
            "This case is a negative capability control: PyBoy reads the halt bit back but the clock advances.",
            "It must not be used as evidence that RTC halt semantics are implemented.",
        ],
        "pc_after": current_pc(pyboy),
    }


def run_rtc_seeded_day_counter_case(pyboy: Any, *, elapsed_days: int, frames: int) -> dict[str, Any]:
    expected_low = int(elapsed_days) % 256
    expected_day_bit = (int(elapsed_days) >> 8) & 0x01
    expected_carry = int(elapsed_days) >= 512
    latch_rtc(pyboy, frames=frames)
    observed_low = read_rtc_register(pyboy, 0x0B, frames=frames)
    observed_high = read_rtc_register(pyboy, 0x0C, frames=frames)
    observed_day_bit = observed_high & 0x01
    observed_carry = (observed_high & 0x80) == 0x80
    observed_halt = (observed_high & 0x40) == 0x40
    expected_case = "carry_overflow" if expected_carry else "no_carry"
    return {
        "case_id": f"rtc_seeded_day_{elapsed_days}_{expected_case}_readback",
        "transition_kind": "rtc_seeded_day_counter_readback",
        "write_range": ".rtc timezero seed,$4000-$5FFF,$6000-$7FFF",
        "seeded_elapsed_days": int(elapsed_days),
        "expected_day_low": expected_low,
        "expected_day_high_day_bit": expected_day_bit,
        "expected_carry": expected_carry,
        "observed_day_low": observed_low,
        "observed_day_high": observed_high,
        "observed_day_high_day_bit": observed_day_bit,
        "observed_carry": observed_carry,
        "observed_halt": observed_halt,
        "day_low_matches": observed_low == expected_low,
        "day_high_day_bit_matches": observed_day_bit == expected_day_bit,
        "carry_matches": observed_carry == expected_carry,
        "halt_semantics_proven": False,
        "transition_observed": (
            observed_low == expected_low
            and observed_day_bit == expected_day_bit
            and observed_carry == expected_carry
            and not observed_halt
        ),
        "known_limits": [
            "This case proves PyBoy readback from a prepared .rtc timezero basis.",
            "It is not a naturally elapsed 512-day runtime replay and does not prove halt semantics.",
        ],
        "pc_after": current_pc(pyboy),
    }


def latch_rtc(pyboy: Any, *, frames: int) -> None:
    execute_absolute_write(pyboy, 0x0000, 0x0A, frames=frames)
    execute_absolute_write(pyboy, 0x6000, 0x00, frames=frames)
    execute_absolute_write(pyboy, 0x6000, 0x01, frames=frames)


def read_rtc_register(pyboy: Any, select_value: int, *, frames: int) -> int:
    execute_absolute_write(pyboy, 0x4000, int(select_value) & 0xFF, frames=frames)
    return read_absolute_byte(pyboy, 0xA000)


def rtc_register_edge_runtime_events(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for seq, case in enumerate(cases):
        if case.get("transition_observed") is not True:
            continue
        events.append(
            runtime_event_envelope(
                event_kind="hardware_event",
                source_kind="pyboy_rtc_runtime",
                source_report="debugger_deity_rtc_register_edge_runtime_replay",
                seq=seq,
                proof_status="runtime_observed",
                observation_type="explicit_hardware_event",
                scope={
                    "backend": "pyboy",
                    "surface": "rtc",
                    "rtc_transition": case.get("transition_kind", ""),
                },
                subjects={
                    "write_range": case.get("write_range", ""),
                    "select_write_address": case.get("select_write_address", ""),
                    "latch_write_address": case.get("latch_write_address", ""),
                },
                precision={
                    "transition_observed": bool(case.get("transition_observed", False)),
                    "halt_semantics_proven": bool(case.get("halt_semantics_proven", False)),
                    "carry_set_readback": case.get("carry_set_readback", False),
                    "carry_clear_readback": case.get("carry_clear_readback", False),
                    "observed_carry": case.get("observed_carry", False),
                    "seeded_elapsed_days": case.get("seeded_elapsed_days", 0),
                },
                validation={
                    "case_id": case.get("case_id", ""),
                    "transition_kind": case.get("transition_kind", ""),
                },
                payload=case,
            )
        )
    return events


NATURAL_INTERRUPT_RUNTIME_CASE_SPECS = [
    {
        "case_id": "vblank_interrupt_entry_exit",
        "interrupt_name": "vblank",
        "vector": 0x0040,
        "exit_pc": 0x016F,
        "ie_bit": 0x01,
    },
    {
        "case_id": "lcd_stat_interrupt_entry_exit",
        "interrupt_name": "lcd_stat",
        "vector": 0x0048,
        "exit_pc": 0x0417,
        "ie_bit": 0x02,
    },
    {
        "case_id": "timer_interrupt_entry_exit",
        "interrupt_name": "timer",
        "vector": 0x0050,
        "exit_pc": 0x0050,
        "ie_bit": 0x04,
    },
]
CONTROLLED_INTERRUPT_RUNTIME_CASE_SPECS = [
    {
        "case_id": "serial_interrupt_entry_exit",
        "interrupt_name": "serial",
        "vector": 0x0058,
        "exit_pc": 0x06F3,
        "ie_bit": 0x08,
    },
    {
        "case_id": "joypad_interrupt_entry_exit",
        "interrupt_name": "joypad",
        "vector": 0x0060,
        "exit_pc": 0x08C3,
        "ie_bit": 0x10,
    },
]
INTERRUPT_RUNTIME_CASE_SPECS = [
    *NATURAL_INTERRUPT_RUNTIME_CASE_SPECS,
    *CONTROLLED_INTERRUPT_RUNTIME_CASE_SPECS,
]


def collect_interrupt_entry_exit_runtime_stream(
    *,
    rom_path: str,
    symbols_path: str,
    frames: int,
    root: Path,
) -> dict[str, Any]:
    rom = resolve_path(rom_path or str(DEFAULT_ROM), root=root)
    sym = resolve_path(symbols_path or str(DEFAULT_SYMBOLS), root=root)
    errors: list[str] = []
    if not rom.exists():
        errors.append(f"missing ROM: {rom_path}")
    if symbols_path and not sym.exists():
        errors.append(f"missing symbols: {symbols_path}")
    if errors:
        return {"kind": "debugger_deity_interrupt_entry_exit_runtime_event_stream", "valid": False, "errors": errors}
    rom_bytes = rom.read_bytes()
    for spec in INTERRUPT_RUNTIME_CASE_SPECS:
        exit_pc = int(spec["exit_pc"])
        if exit_pc >= len(rom_bytes) or rom_bytes[exit_pc] != 0xD9:
            errors.append(f"{spec['case_id']} exit PC ${exit_pc:04X} is not RETI in ROM")
    table = parse_symbol_table(sym) if sym.exists() else {}
    label_by_address = {
        (int(entry["bank"]), int(entry["address"])): label
        for label, entry in table.items()
    }
    PyBoy = rt.load_pyboy("PyBoy required for interrupt runtime replay")
    pyboy = PyBoy(str(rom), window="null", sound=False, log_level="ERROR")
    rt.disable_realtime(pyboy)
    records: list[dict[str, Any]] = []
    counts: dict[tuple[str, str], int] = {}
    hooked: list[tuple[int, int]] = []
    sample_limit = 12

    def record_sample(source_pyboy: Any, case_id: str, phase: str, interrupt_name: str) -> None:
        key = (case_id, phase)
        counts[key] = counts.get(key, 0) + 1
        if sum(1 for item in records if item["case_id"] == case_id and item["phase"] == phase) >= sample_limit:
            return
        records.append(interrupt_runtime_sample(source_pyboy, case_id=case_id, phase=phase, interrupt_name=interrupt_name))

    try:
        for spec in NATURAL_INTERRUPT_RUNTIME_CASE_SPECS:
            case_id = str(spec["case_id"])
            interrupt_name = str(spec["interrupt_name"])
            vector = int(spec["vector"])
            exit_pc = int(spec["exit_pc"])

            same_instruction = vector == exit_pc

            def entry_callback(
                _ctx: Any,
                *,
                cid: str = case_id,
                name: str = interrupt_name,
                same: bool = same_instruction,
            ) -> None:
                record_sample(pyboy, cid, "entry_exit" if same else "entry", name)

            pyboy.hook_register(0, vector, entry_callback, None)
            hooked.append((0, vector))
            if exit_pc != vector:
                def exit_callback(_ctx: Any, *, cid: str = case_id, name: str = interrupt_name) -> None:
                    record_sample(pyboy, cid, "exit", name)

                pyboy.hook_register(0, exit_pc, exit_callback, None)
                hooked.append((0, exit_pc))
        pyboy.tick(max(1, frames), False, False)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"interrupt runtime capture failed: {exc}")
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

    for spec in CONTROLLED_INTERRUPT_RUNTIME_CASE_SPECS:
        errors.extend(
            capture_controlled_interrupt_runtime_case(
                rom=rom,
                spec=spec,
                records=records,
                counts=counts,
                sample_limit=sample_limit,
            )
        )

    cases = [
        build_interrupt_runtime_case(
            spec,
            records=records,
            counts=counts,
            label_by_address=label_by_address,
        )
        for spec in INTERRUPT_RUNTIME_CASE_SPECS
    ]
    runtime_events = interrupt_runtime_events(cases)
    valid = (
        not errors
        and all(case.get("transition_observed") is True for case in cases)
        and len(runtime_events) == len(cases)
    )
    payload = json.dumps({"cases": cases, "runtime_events": runtime_events}, sort_keys=True).encode("utf-8")
    return {
        "kind": "debugger_deity_interrupt_entry_exit_runtime_event_stream",
        "schema_version": 1,
        "valid": valid,
        "backend": "pyboy",
        "rom_path": display_path(rom, root=root),
        "symbols_path": display_path(sym, root=root) if sym.exists() else "",
        "frame_count": max(1, frames),
        "case_count": len(cases),
        "runtime_event_count": len(runtime_events),
        "stream_digest": sha256_bytes(payload),
        "cases": cases,
        "runtime_events": runtime_events,
        "errors": [] if valid else [*errors, "interrupt runtime entry/exit validation failed"],
        "known_limits": [
            "The stream is PyBoy evidence for VBlank, LCD STAT, timer, serial, and joypad interrupt entry/exit.",
            "Serial transfer, cycle-exact IME timing, and timer/LCD mode event streams remain separate proof gaps.",
        ],
    }


def interrupt_runtime_sample(pyboy: Any, *, case_id: str, phase: str, interrupt_name: str) -> dict[str, Any]:
    register_file = pyboy.register_file
    sp = int(register_file.SP) & 0xFFFF
    stack_low = read_absolute_byte(pyboy, sp)
    stack_high = read_absolute_byte(pyboy, (sp + 1) & 0xFFFF)
    return {
        "case_id": case_id,
        "phase": phase,
        "interrupt_name": interrupt_name,
        "frame": int(getattr(pyboy, "frame_count", 0)),
        "pc": int(register_file.PC) & 0xFFFF,
        "sp": sp,
        "stack_top_return_address": stack_low | (stack_high << 8),
        "ie": read_absolute_byte(pyboy, 0xFFFF),
        "if": read_absolute_byte(pyboy, 0xFF0F),
    }


def capture_controlled_interrupt_runtime_case(
    *,
    rom: Path,
    spec: dict[str, Any],
    records: list[dict[str, Any]],
    counts: dict[tuple[str, str], int],
    sample_limit: int,
) -> list[str]:
    errors: list[str] = []
    PyBoy = rt.load_pyboy("PyBoy required for controlled interrupt runtime replay")
    pyboy = PyBoy(str(rom), window="null", sound=False, log_level="ERROR")
    rt.disable_realtime(pyboy)
    hooked: list[tuple[int, int]] = []
    case_id = str(spec["case_id"])
    interrupt_name = str(spec["interrupt_name"])
    vector = int(spec["vector"])
    exit_pc = int(spec["exit_pc"])
    same_instruction = vector == exit_pc

    def record_sample(phase: str) -> None:
        key = (case_id, phase)
        counts[key] = counts.get(key, 0) + 1
        if sum(1 for item in records if item["case_id"] == case_id and item["phase"] == phase) >= sample_limit:
            return
        records.append(interrupt_runtime_sample(pyboy, case_id=case_id, phase=phase, interrupt_name=interrupt_name))

    try:
        pyboy.tick(90, False, False)

        def entry_callback(_ctx: Any) -> None:
            record_sample("entry_exit" if same_instruction else "entry")

        pyboy.hook_register(0, vector, entry_callback, None)
        hooked.append((0, vector))
        if not same_instruction:
            def exit_callback(_ctx: Any) -> None:
                record_sample("exit")

            pyboy.hook_register(0, exit_pc, exit_callback, None)
            hooked.append((0, exit_pc))
        bit = int(spec["ie_bit"]) & 0x1F
        start = 0xFF80
        opcodes = [
            0xF3,                    # di
            0x31, 0x00, 0xD0,        # ld sp,$D000
            0x3E, bit,               # ld a,<interrupt bit>
            0xE0, 0xFF,              # ldh [$FFFF],a
            0xE0, 0x0F,              # ldh [$FF0F],a
            0xFB,                    # ei
            0x00,                    # nop; EI takes effect after the following instruction
            0x3E, bit,               # ld a,<interrupt bit>
            0xE0, 0x0F,              # request one more interrupt after RETI
            0x00,                    # nop
            0x18, 0xFE,              # jr -2
        ]
        for index, opcode in enumerate(opcodes):
            pyboy.memory[start + index] = opcode
        pyboy.register_file.PC = start
        pyboy.register_file.SP = 0xD000
        pyboy.tick(20, False, False)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{case_id} controlled interrupt capture failed: {exc}")
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
    return errors


def build_interrupt_runtime_case(
    spec: dict[str, Any],
    *,
    records: list[dict[str, Any]],
    counts: dict[tuple[str, str], int],
    label_by_address: dict[tuple[int, int], str],
) -> dict[str, Any]:
    case_id = str(spec["case_id"])
    vector = int(spec["vector"])
    exit_pc = int(spec["exit_pc"])
    entry_samples = [
        record
        for record in records
        if record["case_id"] == case_id and record["phase"] in {"entry", "entry_exit"}
    ]
    exit_samples = [
        record
        for record in records
        if record["case_id"] == case_id and record["phase"] in {"exit", "entry_exit"}
    ]
    entry_count = counts.get((case_id, "entry"), 0) + counts.get((case_id, "entry_exit"), 0)
    exit_count = counts.get((case_id, "exit"), 0) + counts.get((case_id, "entry_exit"), 0)
    paired_count = min(entry_count, exit_count)
    compared_pairs = list(zip(entry_samples, exit_samples))
    return_address_consistent = bool(compared_pairs) and all(
        entry.get("stack_top_return_address") == exit.get("stack_top_return_address")
        and entry.get("stack_top_return_address") not in (None, 0)
        for entry, exit in compared_pairs
    )
    return {
        "case_id": case_id,
        "interrupt_name": spec["interrupt_name"],
        "transition_kind": "interrupt_entry_exit",
        "vector": f"${vector:04X}",
        "exit_pc": f"${exit_pc:04X}",
        "vector_label": label_by_address.get((0, vector), ""),
        "exit_label": label_by_address.get((0, exit_pc), ""),
        "ie_bit": int(spec["ie_bit"]),
        "entry_count": entry_count,
        "exit_count": exit_count,
        "paired_entry_exit_count": paired_count,
        "sampled_entry_count": len(entry_samples),
        "sampled_exit_count": len(exit_samples),
        "return_address_consistent": return_address_consistent,
        "entry_samples": entry_samples,
        "exit_samples": exit_samples,
        "transition_observed": entry_count > 0 and exit_count > 0 and paired_count > 0 and return_address_consistent,
    }


def interrupt_runtime_events(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for seq, case in enumerate(cases):
        if case.get("transition_observed") is not True:
            continue
        events.append(
            runtime_event_envelope(
                event_kind="hardware_event",
                source_kind="pyboy_interrupt_runtime",
                source_report="debugger_deity_interrupt_entry_exit_runtime_event_stream",
                seq=seq,
                proof_status="runtime_observed",
                observation_type="explicit_hardware_event",
                scope={
                    "backend": "pyboy",
                    "surface": "interrupts",
                    "interrupt_name": case.get("interrupt_name", ""),
                },
                subjects={
                    "vector": case.get("vector", ""),
                    "exit_pc": case.get("exit_pc", ""),
                    "registers": ["PC", "SP", "IE", "IF"],
                },
                precision={
                    "entry_count": case.get("entry_count", 0),
                    "exit_count": case.get("exit_count", 0),
                    "paired_entry_exit_count": case.get("paired_entry_exit_count", 0),
                    "return_address_consistent": bool(case.get("return_address_consistent", False)),
                    "transition_observed": bool(case.get("transition_observed", False)),
                },
                validation={
                    "case_id": case.get("case_id", ""),
                    "transition_kind": case.get("transition_kind", ""),
                },
                payload=case,
            )
        )
    return events


def collect_timer_lcd_mode_runtime_stream(
    *,
    rom_path: str,
    symbols_path: str,
    frames: int,
    root: Path,
) -> dict[str, Any]:
    rom = resolve_path(rom_path or str(DEFAULT_ROM), root=root)
    sym = resolve_path(symbols_path or str(DEFAULT_SYMBOLS), root=root)
    errors: list[str] = []
    if not rom.exists():
        errors.append(f"missing ROM: {rom_path}")
    if symbols_path and not sym.exists():
        errors.append(f"missing symbols: {symbols_path}")
    if errors:
        return {"kind": "debugger_deity_timer_lcd_mode_runtime_event_stream", "valid": False, "errors": errors}

    PyBoy = rt.load_pyboy("PyBoy required for timer/LCD runtime replay")
    pyboy = PyBoy(str(rom), window="null", sound=False, log_level="ERROR")
    rt.disable_realtime(pyboy)
    try:
        timer_case = run_timer_tima_overflow_runtime_case(pyboy, frames=max(2, frames))
    finally:
        try:
            pyboy.stop(save=False)
        except TypeError:
            pyboy.stop()

    pyboy = PyBoy(str(rom), window="null", sound=False, log_level="ERROR")
    rt.disable_realtime(pyboy)
    try:
        lcd_case = run_lcd_stat_mode_poll_runtime_case(pyboy, frames=max(3, frames))
    finally:
        try:
            pyboy.stop(save=False)
        except TypeError:
            pyboy.stop()

    cases = [timer_case, lcd_case]
    runtime_events = timer_lcd_runtime_events(cases)
    valid = all(case.get("runtime_event_observed") is True for case in cases) and len(runtime_events) == len(cases)
    payload = json.dumps({"cases": cases, "runtime_events": runtime_events}, sort_keys=True).encode("utf-8")
    return {
        "kind": "debugger_deity_timer_lcd_mode_runtime_event_stream",
        "schema_version": 1,
        "valid": valid,
        "backend": "pyboy",
        "rom_path": display_path(rom, root=root),
        "symbols_path": display_path(sym, root=root) if sym.exists() else "",
        "frame_count": max(3, frames),
        "case_count": len(cases),
        "runtime_event_count": len(runtime_events),
        "stream_digest": sha256_bytes(payload),
        "cases": cases,
        "runtime_events": runtime_events,
        "errors": [] if valid else ["timer/LCD runtime event validation failed"],
        "known_limits": [
            "Timer evidence is a CPU polling loop observing TIMA wrap/drop and IF timer-bit request, not a cycle-exact reload timestamp.",
            "LCD evidence is a CPU polling loop observing STAT mode and LY transitions, not full PPU dot timing.",
            "Cross-backend timer/LCD parity remains out of scope.",
        ],
    }


def run_timer_tima_overflow_runtime_case(pyboy: Any, *, frames: int) -> dict[str, Any]:
    sample_count = 0x80
    buffer = 0xC000
    tma = 0xA5
    initial_tima = 0xF0
    tac = 0x05
    opcodes = [
        0xF3,
        0x31, 0xFF, 0xDF,
        0x3E, 0x04,
        0xE0, 0xFF,
        0x3E, tma,
        0xE0, 0x06,
        0x3E, initial_tima,
        0xE0, 0x05,
        0x3E, tac,
        0xE0, 0x07,
        0xAF,
        0xE0, 0x0F,
        0x21, buffer & 0xFF, (buffer >> 8) & 0xFF,
        0x06, sample_count,
        0xF0, 0x05,
        0x22,
        0xF0, 0x0F,
        0x22,
        0x05,
        0x20, 0xF7,
        0x18, 0xFE,
    ]
    execute_hram_snippet(pyboy, opcodes, frames=frames)
    samples = [
        {
            "sample_index": index,
            "tima": read_absolute_byte(pyboy, buffer + index * 2),
            "if": read_absolute_byte(pyboy, buffer + index * 2 + 1),
        }
        for index in range(sample_count)
    ]
    drops = [
        {
            "before_index": index,
            "before_tima": samples[index]["tima"],
            "after_index": index + 1,
            "after_tima": samples[index + 1]["tima"],
            "after_if": samples[index + 1]["if"],
        }
        for index in range(len(samples) - 1)
        if samples[index + 1]["tima"] < samples[index]["tima"]
    ]
    first_interrupt_index = next(
        (sample["sample_index"] for sample in samples if sample["if"] & 0x04),
        None,
    )
    overflow_drop_observed = any(item["after_if"] & 0x04 for item in drops)
    interrupt_request_observed = first_interrupt_index is not None
    return {
        "case_id": "timer_tima_overflow_interrupt_request",
        "event_family": "timer",
        "transition_kind": "timer_tima_overflow_if_request",
        "registers": ["FF05", "FF06", "FF07", "FF0F", "FFFF"],
        "sample_count": sample_count,
        "tma": tma,
        "initial_tima": initial_tima,
        "tac": tac,
        "if_timer_bit": 0x04,
        "first_interrupt_request_sample": first_interrupt_index,
        "overflow_drop_count": len(drops),
        "overflow_drop_samples": drops[:8],
        "sample_head": samples[:12],
        "sample_tail": samples[-12:],
        "overflow_drop_observed": overflow_drop_observed,
        "interrupt_request_observed": interrupt_request_observed,
        "runtime_event_observed": overflow_drop_observed and interrupt_request_observed,
        "pc_after": current_pc(pyboy),
    }


def run_lcd_stat_mode_poll_runtime_case(pyboy: Any, *, frames: int) -> dict[str, Any]:
    outer_count = 0x05
    inner_count = 0x100
    sample_count = outer_count * inner_count
    buffer = 0xC200
    opcodes = [
        0xF3,
        0x3E, 0x91,
        0xE0, 0x40,
        0x21, buffer & 0xFF, (buffer >> 8) & 0xFF,
        0x0E, outer_count,
        0x06, 0x00,
        0xF0, 0x41,
        0x22,
        0xF0, 0x44,
        0x22,
        0x05,
        0x20, 0xF7,
        0x0D,
        0x20, 0xF2,
        0x18, 0xFE,
    ]
    execute_hram_snippet(pyboy, opcodes, frames=frames)
    samples = [
        {
            "sample_index": index,
            "stat": read_absolute_byte(pyboy, buffer + index * 2),
            "mode": read_absolute_byte(pyboy, buffer + index * 2) & 0x03,
            "ly": read_absolute_byte(pyboy, buffer + index * 2 + 1),
        }
        for index in range(sample_count)
    ]
    observed_modes = sorted({sample["mode"] for sample in samples})
    mode_counts = {
        str(mode): sum(1 for sample in samples if sample["mode"] == mode)
        for mode in observed_modes
    }
    transitions = [
        {
            "from_index": index,
            "from_mode": samples[index]["mode"],
            "from_ly": samples[index]["ly"],
            "to_index": index + 1,
            "to_mode": samples[index + 1]["mode"],
            "to_ly": samples[index + 1]["ly"],
        }
        for index in range(len(samples) - 1)
        if (samples[index]["mode"], samples[index]["ly"]) != (samples[index + 1]["mode"], samples[index + 1]["ly"])
    ]
    vblank_entry = next(
        (
            {"sample_index": sample["sample_index"], "mode": sample["mode"], "ly": sample["ly"]}
            for sample in samples
            if sample["mode"] == 1 and sample["ly"] >= 144
        ),
        {},
    )
    mode_sequence_observed = {0, 1, 2, 3}.issubset(set(observed_modes))
    ly_max = max(sample["ly"] for sample in samples) if samples else 0
    return {
        "case_id": "lcd_stat_mode_poll_sequence",
        "event_family": "lcd",
        "transition_kind": "lcd_stat_mode_ly_sequence",
        "registers": ["FF40", "FF41", "FF44"],
        "sample_count": sample_count,
        "observed_modes": observed_modes,
        "mode_counts": mode_counts,
        "ly_min": min(sample["ly"] for sample in samples) if samples else 0,
        "ly_max": ly_max,
        "vblank_entry": vblank_entry,
        "transition_count": len(transitions),
        "transition_samples": transitions[:96],
        "sample_head": samples[:12],
        "sample_tail": samples[-12:],
        "mode_sequence_observed": mode_sequence_observed,
        "vblank_observed": bool(vblank_entry),
        "runtime_event_observed": mode_sequence_observed and bool(vblank_entry) and ly_max >= 144,
        "pc_after": current_pc(pyboy),
    }


def timer_lcd_runtime_events(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for seq, case in enumerate(cases):
        if case.get("runtime_event_observed") is not True:
            continue
        event_family = str(case.get("event_family", ""))
        if event_family == "timer":
            precision = {
                "sample_count": case.get("sample_count", 0),
                "overflow_drop_observed": bool(case.get("overflow_drop_observed", False)),
                "interrupt_request_observed": bool(case.get("interrupt_request_observed", False)),
                "overflow_drop_count": case.get("overflow_drop_count", 0),
            }
        else:
            precision = {
                "sample_count": case.get("sample_count", 0),
                "observed_modes": case.get("observed_modes", []),
                "mode_sequence_observed": bool(case.get("mode_sequence_observed", False)),
                "vblank_observed": bool(case.get("vblank_observed", False)),
                "transition_count": case.get("transition_count", 0),
            }
        events.append(
            runtime_event_envelope(
                event_kind="hardware_event",
                source_kind="pyboy_timer_lcd_runtime",
                source_report="debugger_deity_timer_lcd_mode_runtime_event_stream",
                seq=seq,
                proof_status="runtime_observed",
                observation_type="explicit_hardware_event",
                scope={"backend": "pyboy", "surface": "timer_lcd", "event_family": event_family},
                subjects={"registers": case.get("registers", [])},
                precision=precision,
                validation={
                    "case_id": case.get("case_id", ""),
                    "transition_kind": case.get("transition_kind", ""),
                },
                payload=case,
            )
        )
    return events


def collect_serial_transfer_runtime_stream(
    *,
    rom_path: str,
    symbols_path: str,
    frames: int,
    root: Path,
) -> dict[str, Any]:
    rom = resolve_path(rom_path or str(DEFAULT_ROM), root=root)
    sym = resolve_path(symbols_path or str(DEFAULT_SYMBOLS), root=root)
    errors: list[str] = []
    if not rom.exists():
        errors.append(f"missing ROM: {rom_path}")
    if symbols_path and not sym.exists():
        errors.append(f"missing symbols: {symbols_path}")
    if errors:
        return {"kind": "debugger_deity_serial_transfer_runtime_event_stream", "valid": False, "errors": errors}

    PyBoy = rt.load_pyboy("PyBoy required for serial runtime replay")
    cases: list[dict[str, Any]] = []
    for case_id, byte_value in (
        ("serial_internal_clock_transfer_byte_42", 0x42),
        ("serial_internal_clock_transfer_byte_5a", 0x5A),
    ):
        pyboy = PyBoy(str(rom), window="null", sound=False, log_level="ERROR")
        rt.disable_realtime(pyboy)
        try:
            cases.append(
                run_serial_internal_clock_transfer_case(
                    pyboy,
                    case_id=case_id,
                    outgoing_byte=byte_value,
                    frames=max(5, frames),
                )
            )
        finally:
            try:
                pyboy.stop(save=False)
            except TypeError:
                pyboy.stop()

    runtime_events = serial_transfer_runtime_events(cases)
    valid = all(case.get("runtime_event_observed") is True for case in cases) and len(runtime_events) == len(cases)
    payload = json.dumps({"cases": cases, "runtime_events": runtime_events}, sort_keys=True).encode("utf-8")
    return {
        "kind": "debugger_deity_serial_transfer_runtime_event_stream",
        "schema_version": 1,
        "valid": valid,
        "backend": "pyboy",
        "rom_path": display_path(rom, root=root),
        "symbols_path": display_path(sym, root=root) if sym.exists() else "",
        "frame_count": max(5, frames),
        "case_count": len(cases),
        "runtime_event_count": len(runtime_events),
        "stream_digest": sha256_bytes(payload),
        "cases": cases,
        "runtime_events": runtime_events,
        "errors": [] if valid else ["serial transfer runtime event validation failed"],
        "known_limits": [
            "The stream observes PyBoy's internal-clock transfer path after a controlled SB/SC setup.",
            "Disconnected-peer receive behavior is recorded as observed emulator behavior, not a real link partner claim.",
            "Cable timing, peer negotiation, Mystery Gift protocol flow, and cross-backend serial parity remain out of scope.",
        ],
    }


def run_serial_internal_clock_transfer_case(
    pyboy: Any,
    *,
    case_id: str,
    outgoing_byte: int,
    frames: int,
) -> dict[str, Any]:
    sample_count = 0x80
    buffer = 0xC400
    outgoing_byte &= 0xFF
    opcodes = [
        0xF3,
        0x31, 0xFF, 0xDF,
        0x3E, 0x08,
        0xE0, 0xFF,
        0xAF,
        0xE0, 0x0F,
        0x3E, outgoing_byte,
        0xE0, 0x01,
        0x3E, 0x81,
        0xE0, 0x02,
        0x21, buffer & 0xFF, (buffer >> 8) & 0xFF,
        0x06, sample_count,
        0xF0, 0x01,
        0x22,
        0xF0, 0x02,
        0x22,
        0xF0, 0x0F,
        0x22,
        0x05,
        0x20, 0xF4,
        0x18, 0xFE,
    ]
    execute_hram_snippet(pyboy, opcodes, frames=frames)
    samples = [
        {
            "sample_index": index,
            "sb": read_absolute_byte(pyboy, buffer + index * 3),
            "sc": read_absolute_byte(pyboy, buffer + index * 3 + 1),
            "if": read_absolute_byte(pyboy, buffer + index * 3 + 2),
        }
        for index in range(sample_count)
    ]
    serial_output = str(pyboy._serial())
    sc_values = sorted({sample["sc"] for sample in samples})
    sb_values = sorted({sample["sb"] for sample in samples})
    first_if_index = next((sample["sample_index"] for sample in samples if sample["if"] & 0x08), None)
    start_observed = any(sample["sc"] == 0x81 for sample in samples)
    post_start_observed = any(sample["sc"] != 0x81 for sample in samples)
    interrupt_request_observed = first_if_index is not None
    serial_output_observed = chr(outgoing_byte) in serial_output
    receive_fill_observed = any(sample["sb"] == 0xFF for sample in samples)
    return {
        "case_id": case_id,
        "event_family": "serial",
        "transition_kind": "serial_internal_clock_transfer",
        "registers": ["FF01", "FF02", "FF0F", "FFFF"],
        "sample_count": sample_count,
        "outgoing_byte": outgoing_byte,
        "outgoing_char": chr(outgoing_byte),
        "serial_output": serial_output,
        "sc_values": sc_values,
        "sb_values": sb_values,
        "first_interrupt_request_sample": first_if_index,
        "if_serial_bit": 0x08,
        "sample_head": samples[:16],
        "sample_tail": samples[-16:],
        "start_observed": start_observed,
        "post_start_observed": post_start_observed,
        "interrupt_request_observed": interrupt_request_observed,
        "serial_output_observed": serial_output_observed,
        "receive_fill_observed": receive_fill_observed,
        "runtime_event_observed": (
            start_observed
            and post_start_observed
            and interrupt_request_observed
            and serial_output_observed
            and receive_fill_observed
        ),
        "pc_after": current_pc(pyboy),
    }


def serial_transfer_runtime_events(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for seq, case in enumerate(cases):
        if case.get("runtime_event_observed") is not True:
            continue
        events.append(
            runtime_event_envelope(
                event_kind="hardware_event",
                source_kind="pyboy_serial_runtime",
                source_report="debugger_deity_serial_transfer_runtime_event_stream",
                seq=seq,
                proof_status="runtime_observed",
                observation_type="explicit_hardware_event",
                scope={"backend": "pyboy", "surface": "serial", "event_family": "serial_transfer"},
                subjects={"registers": case.get("registers", [])},
                precision={
                    "sample_count": case.get("sample_count", 0),
                    "outgoing_byte": case.get("outgoing_byte", 0),
                    "start_observed": bool(case.get("start_observed", False)),
                    "post_start_observed": bool(case.get("post_start_observed", False)),
                    "interrupt_request_observed": bool(case.get("interrupt_request_observed", False)),
                    "serial_output_observed": bool(case.get("serial_output_observed", False)),
                    "receive_fill_observed": bool(case.get("receive_fill_observed", False)),
                },
                validation={
                    "case_id": case.get("case_id", ""),
                    "transition_kind": case.get("transition_kind", ""),
                },
                payload=case,
            )
        )
    return events


def collect_script_map_content_runtime_replays(
    *,
    rom_path: str,
    symbols_path: str,
    frames: int,
    root: Path,
) -> dict[str, Any]:
    rom = resolve_path(rom_path or str(DEFAULT_ROM), root=root)
    sym = resolve_path(symbols_path or str(DEFAULT_SYMBOLS), root=root)
    materializer_path = root / "audit" / "debugger_literal_anything" / "script_map_content_materializers.json"
    errors: list[str] = []
    if not rom.exists():
        errors.append(f"missing ROM: {rom_path}")
    if symbols_path and not sym.exists():
        errors.append(f"missing symbols: {symbols_path}")
    materializers: dict[str, Any] = {}
    if not materializer_path.exists():
        errors.append(f"missing materializer artifact: {display_path(materializer_path, root=root)}")
    else:
        try:
            materializers = json.loads(materializer_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"materializer artifact unreadable: {exc}")
    if errors:
        return {"kind": "debugger_deity_script_map_content_runtime_replays", "valid": False, "errors": errors}
    symbol_table = parse_symbol_table(sym)
    materialization_by_id = {
        str(item.get("scenario_id", "")): item
        for item in materializers.get("materializations", [])
        if isinstance(item, dict)
    }
    try:
        from tools.debugger.content_state import load_map_index
    except Exception as exc:  # noqa: BLE001
        return {
            "kind": "debugger_deity_script_map_content_runtime_replays",
            "valid": False,
            "errors": [f"content-state helpers unavailable: {type(exc).__name__}: {exc}"],
        }
    map_index, map_errors = load_map_index(root=root)
    errors.extend(map_errors)
    warp_materialization = materialization_by_id.get("content_scenario_1_0000", {})
    object_materialization = materialization_by_id.get("content_scenario_1_0019", {})
    if not isinstance(warp_materialization, dict) or warp_materialization.get("status") != "ready":
        errors.append("content_scenario_1_0000 warp materialization is not ready")
    if not isinstance(object_materialization, dict) or object_materialization.get("status") != "ready":
        errors.append("content_scenario_1_0019 object materialization is not ready")
    if errors:
        return {"kind": "debugger_deity_script_map_content_runtime_replays", "valid": False, "errors": errors}

    warp_case = run_azalea_warp_runtime_case(
        rom=rom,
        symbol_table=symbol_table,
        map_index=map_index,
        materialization=warp_materialization,
        frames=max(1, frames),
    )
    object_case = run_azalea_object_runtime_case(
        rom=rom,
        symbol_table=symbol_table,
        materialization=object_materialization,
        frames=max(1, frames),
    )
    cases = [warp_case, object_case]
    runtime_events = script_map_content_runtime_events(cases)
    valid = (
        all(case.get("transition_observed") is True for case in cases)
        and len(runtime_events) == len(cases)
    )
    payload = json.dumps({"cases": cases, "runtime_events": runtime_events}, sort_keys=True).encode("utf-8")
    return {
        "kind": "debugger_deity_script_map_content_runtime_replays",
        "schema_version": 1,
        "valid": valid,
        "backend": "pyboy",
        "rom_path": display_path(rom, root=root),
        "symbols_path": display_path(sym, root=root),
        "materializer_path": display_path(materializer_path, root=root),
        "frame_count": max(1, frames),
        "case_count": len(cases),
        "runtime_event_count": len(runtime_events),
        "stream_digest": sha256_bytes(payload),
        "cases": cases,
        "runtime_events": runtime_events,
        "errors": [] if valid else ["script/map content runtime replay validation failed"],
        "known_limits": [
            "The selected warp and object cases execute ROM helper routines from synthesized WRAM state.",
            "This is not a full overworld button/input flow replay and does not claim all map collisions or all object events.",
        ],
    }


def run_azalea_warp_runtime_case(
    *,
    rom: Path,
    symbol_table: dict[str, dict[str, Any]],
    map_index: dict[str, dict[str, Any]],
    materialization: dict[str, Any],
    frames: int,
) -> dict[str, Any]:
    values = materialization.get("values", {}) if isinstance(materialization.get("values"), dict) else {}
    source_map = str(values.get("map_name") or values.get("map_label") or "AzaleaTown_MapEvents")
    destination_map = str(values.get("destination_map") or "")
    destination_warp = int(str(values.get("destination_warp") or "0"), 0)
    source_entry = dict_value(materialization.get("map_resolution"))
    destination_entry = map_index_entry_for_label(map_index, destination_map)
    source_group = int(source_entry.get("map_group", 0) or 0)
    source_number = int(source_entry.get("map_number", 0) or 0)
    destination_group = int(destination_entry.get("map_group", 0) or 0)
    destination_number = int(destination_entry.get("map_number", 0) or 0)
    x = int(str(values.get("x") or "0"), 0)
    y = int(str(values.get("y") or "0"), 0)
    PyBoy = rt.load_pyboy("PyBoy required for script/map content runtime replay")
    pyboy = PyBoy(str(rom), window="null", sound=False, log_level="ERROR")
    rt.disable_realtime(pyboy)
    hooks: list[dict[str, Any]] = []
    hooked: list[tuple[int, int]] = []
    try:
        pyboy.tick(120, False, False)
        for label in ("WarpCheck", "EnterMapWarp"):
            entry = symbol_table[label]

            def callback(_ctx: Any, *, name: str = label, address: int = int(entry["address"])) -> None:
                hooks.append(runtime_helper_hook_sample(pyboy, label=name, address=address))

            pyboy.hook_register(int(entry["bank"]), int(entry["address"]), callback, None)
            hooked.append((int(entry["bank"]), int(entry["address"])))
        warp_table = 0xD300
        for offset, value in enumerate([y, x, destination_warp, destination_group, destination_number]):
            write_bank_byte(pyboy, symbol_table=symbol_table, address=warp_table + offset, value=value)
        write_symbol_byte(pyboy, symbol_table, "wPlayerTileCollision", 0x71)
        write_symbol_byte(pyboy, symbol_table, "wPlayerMapX", x + 4)
        write_symbol_byte(pyboy, symbol_table, "wPlayerMapY", y + 4)
        write_symbol_byte(pyboy, symbol_table, "wMapScriptsBank", int(symbol_table["AzaleaTown_MapEvents"]["bank"]))
        write_symbol_byte(pyboy, symbol_table, "hROMBank", 1)
        write_symbol_byte(pyboy, symbol_table, "wCurMapWarpEventCount", 1)
        write_symbol_byte(pyboy, symbol_table, "wCurMapWarpEventsPointer", warp_table & 0xFF)
        write_symbol_address_byte(pyboy, symbol_table, "wCurMapWarpEventsPointer", 1, (warp_table >> 8) & 0xFF)
        write_symbol_byte(pyboy, symbol_table, "wMapGroup", source_group)
        write_symbol_byte(pyboy, symbol_table, "wMapNumber", source_number)
        before = read_symbols(
            pyboy,
            symbol_table=symbol_table,
            symbols=("wMapGroup", "wMapNumber", "wNextWarp", "wNextMapGroup", "wNextMapNumber"),
        )
        execute_rom0_call(pyboy, symbol_table=symbol_table, label="WarpCheck", frames=frames)
        after_warp_check = read_symbols(
            pyboy,
            symbol_table=symbol_table,
            symbols=("wNextWarp", "wNextMapGroup", "wNextMapNumber", "wPrevWarp", "wPrevMapGroup", "wPrevMapNumber"),
        )
        warp_carry = bool(int(pyboy.register_file.F) & 0x10)
        execute_rom0_call(pyboy, symbol_table=symbol_table, label="EnterMapWarp", frames=frames)
        after_enter = read_symbols(
            pyboy,
            symbol_table=symbol_table,
            symbols=("wWarpNumber", "wMapGroup", "wMapNumber"),
        )
        enter_carry = bool(int(pyboy.register_file.F) & 0x10)
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
    helper_hits = helper_hit_counts(hooks)
    transition_observed = (
        warp_carry
        and after_warp_check.get("wNextWarp") == destination_warp
        and after_warp_check.get("wNextMapGroup") == destination_group
        and after_warp_check.get("wNextMapNumber") == destination_number
        and after_enter.get("wWarpNumber") == destination_warp
        and after_enter.get("wMapGroup") == destination_group
        and after_enter.get("wMapNumber") == destination_number
        and helper_hits.get("WarpCheck", 0) > 0
        and helper_hits.get("EnterMapWarp", 0) > 0
    )
    return {
        "case_id": "azalea_pokecenter_warp_runtime",
        "scenario_id": "content_scenario_1_0000",
        "transition_kind": "warp_collision_dispatch",
        "source_map": source_map,
        "destination_map": destination_map,
        "destination_resolved_map": str(destination_entry.get("map_name", "") or ""),
        "destination_warp": destination_warp,
        "source_position": {"x": x, "y": y, "player_map_x": x + 4, "player_map_y": y + 4},
        "before": before,
        "after_warp_check": after_warp_check,
        "after_enter_map_warp": after_enter,
        "helper_hits": helper_hits,
        "helper_samples": hooks[:12],
        "warp_check_carry": warp_carry,
        "enter_map_warp_carry": enter_carry,
        "carry_observed": warp_carry,
        "transition_observed": transition_observed,
    }


def run_azalea_object_runtime_case(
    *,
    rom: Path,
    symbol_table: dict[str, dict[str, Any]],
    materialization: dict[str, Any],
    frames: int,
) -> dict[str, Any]:
    values = materialization.get("values", {}) if isinstance(materialization.get("values"), dict) else {}
    visibility = materialization.get("object_visibility_materializer", {})
    visibility_patches = list_value(visibility.get("patches") if isinstance(visibility, dict) else None)
    script_label = str(values.get("script") or "AzaleaTownRocket1Script")
    script_entry = symbol_table[script_label]
    object_x = int(visibility.get("source_values", {}).get("x", values.get("x", 0)) if isinstance(visibility, dict) else values.get("x", 0))
    object_y = int(visibility.get("source_values", {}).get("y", values.get("y", 0)) if isinstance(visibility, dict) else values.get("y", 0))
    map_object_index = int(visibility.get("map_object_index", 0) or 0) if isinstance(visibility, dict) else 0
    PyBoy = rt.load_pyboy("PyBoy required for script/map content runtime replay")
    pyboy = PyBoy(str(rom), window="null", sound=False, log_level="ERROR")
    rt.disable_realtime(pyboy)
    hooks: list[dict[str, Any]] = []
    hooked: list[tuple[int, int]] = []
    try:
        pyboy.tick(120, False, False)
        for label in ("TryObjectEvent", "CheckFacingObject", "CallScript"):
            entry = symbol_table[label]

            def callback(_ctx: Any, *, name: str = label, address: int = int(entry["address"])) -> None:
                hooks.append(runtime_helper_hook_sample(pyboy, label=name, address=address))

            pyboy.hook_register(int(entry["bank"]), int(entry["address"]), callback, None)
            hooked.append((int(entry["bank"]), int(entry["address"])))
        for patch in visibility_patches:
            if isinstance(patch, dict):
                write_bank_byte(
                    pyboy,
                    symbol_table=symbol_table,
                    address=int(patch.get("address", 0) or 0),
                    value=int(patch.get("value", 0) or 0),
                    bank=int(patch.get("bank", 1) or 1),
                )
        write_symbol_byte(pyboy, symbol_table, "wMapScriptsBank", int(script_entry["bank"]))
        write_symbol_byte(pyboy, symbol_table, "wPlayerMapX", object_x + 4)
        write_symbol_byte(pyboy, symbol_table, "wPlayerMapY", object_y + 3)
        write_symbol_byte(pyboy, symbol_table, "wPlayerDirection", 0)
        for symbol in ("wScriptBank", "wScriptPos", "wScriptRunning", "hLastTalked", "hObjectStructIndex", "hMapObjectIndex"):
            write_symbol_byte(pyboy, symbol_table, symbol, 0)
        before = read_symbols(
            pyboy,
            symbol_table=symbol_table,
            symbols=("wObject1Sprite", "wObject1MapObjectIndex", "wObject1MapX", "wObject1MapY", "wObject1Walking"),
        )
        pyboy.memory[0x2000] = int(symbol_table["TryObjectEvent"]["bank"])
        write_symbol_byte(pyboy, symbol_table, "hROMBank", int(symbol_table["TryObjectEvent"]["bank"]))
        execute_bank_call(pyboy, symbol_table=symbol_table, label="TryObjectEvent", frames=frames)
        after = read_symbols(
            pyboy,
            symbol_table=symbol_table,
            symbols=("wScriptBank", "wScriptPos", "wScriptRunning", "hLastTalked", "hObjectStructIndex", "hMapObjectIndex"),
        )
        script_pos = after.get("wScriptPos", 0) | (
            read_symbol_address_byte(pyboy, symbol_table, "wScriptPos", 1) << 8
        )
        carry = bool(int(pyboy.register_file.F) & 0x10)
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
    helper_hits = helper_hit_counts(hooks)
    transition_observed = (
        carry
        and after.get("wScriptBank") == int(script_entry["bank"])
        and script_pos == int(script_entry["address"])
        and after.get("wScriptRunning") == 0xFF
        and after.get("hLastTalked") == map_object_index
        and helper_hits.get("TryObjectEvent", 0) > 0
        and helper_hits.get("CheckFacingObject", 0) > 0
        and helper_hits.get("CallScript", 0) > 0
    )
    return {
        "case_id": "azalea_rocket_object_runtime",
        "scenario_id": "content_scenario_1_0019",
        "transition_kind": "object_facing_script_dispatch",
        "source_map": str(values.get("map_label") or "AzaleaTown_MapEvents"),
        "script_label": script_label,
        "expected_script_bank": int(script_entry["bank"]),
        "expected_script_address": int(script_entry["address"]),
        "map_object_index": map_object_index,
        "player_position": {"player_map_x": object_x + 4, "player_map_y": object_y + 3, "direction": "down"},
        "object_position": {"object_map_x": object_x + 4, "object_map_y": object_y + 4},
        "before": before,
        "after": {**after, "wScriptPosWord": script_pos},
        "helper_hits": helper_hits,
        "helper_samples": hooks[:12],
        "try_object_event_carry": carry,
        "carry_observed": carry,
        "transition_observed": transition_observed,
    }


def execute_rom0_call(pyboy: Any, *, symbol_table: dict[str, dict[str, Any]], label: str, frames: int) -> None:
    execute_call(pyboy, address=int(symbol_table[label]["address"]), frames=frames)


def execute_bank_call(pyboy: Any, *, symbol_table: dict[str, dict[str, Any]], label: str, frames: int) -> None:
    execute_call(pyboy, address=int(symbol_table[label]["address"]), frames=frames)


def execute_call(pyboy: Any, *, address: int, frames: int) -> None:
    start = 0xFF80
    opcodes = [0xF3, 0xCD, address & 0xFF, (address >> 8) & 0xFF, 0x18, 0xFE]
    for index, opcode in enumerate(opcodes):
        pyboy.memory[start + index] = opcode
    pyboy.memory[0xFFFF] = 0
    pyboy.memory[0xFF0F] = 0
    pyboy.register_file.PC = start
    pyboy.register_file.SP = 0xDFFF
    tick_pyboy(pyboy, frames)


def runtime_helper_hook_sample(pyboy: Any, *, label: str, address: int) -> dict[str, Any]:
    return {
        "label": label,
        "address": f"${address:04X}",
        "frame": int(getattr(pyboy, "frame_count", 0)),
        "pc": int(pyboy.register_file.PC) & 0xFFFF,
        "sp": int(pyboy.register_file.SP) & 0xFFFF,
    }


def helper_hit_counts(samples: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for sample in samples:
        label = str(sample.get("label", ""))
        counts[label] = counts.get(label, 0) + 1
    return counts


def map_index_entry_for_label(map_index: dict[str, dict[str, Any]], label: str) -> dict[str, Any]:
    text = str(label or "")
    if text in map_index:
        return map_index[text]
    for prefix in ("MAP_", "GROUP_"):
        if text.startswith(prefix):
            text = text[len(prefix):]
            break
    return map_index.get(map_constant_to_symbol_name(text), {})


def map_constant_to_symbol_name(value: str) -> str:
    converted: list[str] = []
    for part in (part for part in str(value or "").split("_") if part):
        if part[0].isdigit():
            converted.append(part.upper())
        else:
            converted.append(part[:1].upper() + part[1:].lower())
    return "".join(converted)


def write_symbol_byte(pyboy: Any, symbol_table: dict[str, dict[str, Any]], symbol: str, value: int) -> None:
    entry = symbol_table[symbol]
    write_bank_byte(pyboy, symbol_table=symbol_table, address=int(entry["address"]), value=value, bank=int(entry["bank"]))


def read_symbol_address_byte(pyboy: Any, symbol_table: dict[str, dict[str, Any]], symbol: str, offset: int) -> int:
    entry = symbol_table[symbol]
    return read_bank_byte(pyboy, address=int(entry["address"]) + offset, bank=int(entry["bank"]))


def write_symbol_address_byte(
    pyboy: Any,
    symbol_table: dict[str, dict[str, Any]],
    symbol: str,
    offset: int,
    value: int,
) -> None:
    entry = symbol_table[symbol]
    write_bank_byte(pyboy, symbol_table=symbol_table, address=int(entry["address"]) + offset, value=value, bank=int(entry["bank"]))


def read_symbols(pyboy: Any, *, symbol_table: dict[str, dict[str, Any]], symbols: tuple[str, ...]) -> dict[str, int]:
    return {
        symbol: read_symbol_address_byte(pyboy, symbol_table, symbol, 0)
        for symbol in symbols
    }


def write_bank_byte(
    pyboy: Any,
    *,
    symbol_table: dict[str, dict[str, Any]],
    address: int,
    value: int,
    bank: int = 1,
) -> None:
    if 0xD000 <= address <= 0xDFFF and bank:
        try:
            pyboy.memory[bank, address] = int(value) & 0xFF
            return
        except Exception:
            old_bank = int(pyboy.memory[0xFF70])
            pyboy.memory[0xFF70] = bank
            try:
                pyboy.memory[address] = int(value) & 0xFF
            finally:
                pyboy.memory[0xFF70] = old_bank
            return
    pyboy.memory[address] = int(value) & 0xFF


def read_bank_byte(pyboy: Any, *, address: int, bank: int = 1) -> int:
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


def dict_value(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def list_value(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def script_map_content_runtime_events(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for seq, case in enumerate(cases):
        if case.get("transition_observed") is not True:
            continue
        events.append(
            runtime_event_envelope(
                event_kind="control_flow",
                source_kind="pyboy_script_map_content_runtime",
                source_report="debugger_deity_script_map_content_runtime_replays",
                seq=seq,
                proof_status="runtime_observed",
                observation_type="instruction_pre_state",
                scope={
                    "backend": "pyboy",
                    "surface": "script_map_content",
                    "scenario_id": case.get("scenario_id", ""),
                },
                subjects={
                    "helpers": sorted(case.get("helper_hits", {}).keys()),
                    "source_map": case.get("source_map", ""),
                },
                precision={
                    "transition_observed": bool(case.get("transition_observed", False)),
                    "helper_hit_count": sum(int(value) for value in case.get("helper_hits", {}).values()),
                },
                validation={
                    "case_id": case.get("case_id", ""),
                    "transition_kind": case.get("transition_kind", ""),
                },
                payload=case,
            )
        )
    return events


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
    runtime_events = script_vm_stream_events(
        rows,
        script_label=script_label,
        source_report="debugger_deity_script_vm_stream",
    )
    payload = json.dumps(
        {"rows": rows, "runtime_events": runtime_events},
        sort_keys=True,
    ).encode("utf-8")
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
        "runtime_event_count": len(runtime_events),
        "runtime_events": runtime_events,
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


def apu_register_timeline_events(
    rows: list[dict[str, Any]],
    *,
    species: str,
    source_report: str,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    previous: dict[str, Any] = {}
    for row in rows:
        apu = dict(row.get("apu") or {})
        if not apu:
            previous = apu
            continue
        changed_registers = sorted(
            name
            for name, value in apu.items()
            if not previous or previous.get(name) != value
        )
        if not changed_registers:
            previous = apu
            continue
        pc = row.get("pc")
        pc_bank_address = f"??:{int(pc):04X}" if isinstance(pc, int) else ""
        events.append(
            runtime_event_envelope(
                event_kind="apu",
                source_kind="cry_apu_timeline",
                source_report=source_report,
                seq=len(events),
                frame=int(row.get("frame", 0) or 0),
                pc_bank_address=pc_bank_address,
                proof_status="runtime_observed",
                observation_type="explicit_hardware_event",
                scope={"surface": "audio", "species": species},
                subjects={
                    "hardware_registers": sorted(apu),
                    "changed_registers": changed_registers,
                },
                precision={
                    "backend": "pyboy",
                    "timing": "per_tick_apu_register_sample",
                    "address_space": "game_boy_apu_ff10_ff26",
                },
                validation={
                    "changed_register_count": len(changed_registers),
                    "frame_sample": row.get("frame", 0),
                },
                payload={
                    "registers": apu,
                    "changed_registers": changed_registers,
                },
            )
        )
        previous = apu
    return events


def script_vm_stream_events(
    rows: list[dict[str, Any]],
    *,
    script_label: str,
    source_report: str,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    previous: dict[str, Any] = {}
    tracked_fields = (
        "script_bank",
        "script_pos",
        "script_mode",
        "script_running",
        "script_stack_size",
        "pc",
    )
    for row in rows:
        changed_fields = [
            field
            for field in tracked_fields
            if not previous or previous.get(field) != row.get(field)
        ]
        if not changed_fields:
            previous = row
            continue
        pc = row.get("pc")
        pc_bank_address = f"??:{int(pc):04X}" if isinstance(pc, int) else ""
        script_bank = row.get("script_bank")
        script_pos = row.get("script_pos")
        script_address = ""
        if isinstance(script_bank, int) and isinstance(script_pos, int):
            script_address = f"{script_bank:02X}:{script_pos:04X}"
        events.append(
            runtime_event_envelope(
                event_kind="script_vm",
                source_kind="script_vm_stream",
                source_report=source_report,
                seq=len(events),
                frame=int(row.get("frame", 0) or 0),
                pc_bank_address=pc_bank_address,
                proof_status="runtime_observed",
                observation_type="frame_sample",
                scope={"surface": "script", "script_label": script_label},
                subjects={
                    "scripts": [script_label],
                    "script_address": script_address,
                    "changed_fields": changed_fields,
                },
                precision={
                    "backend": "pyboy",
                    "timing": "per_tick_script_vm_sample",
                    "state_fields": list(tracked_fields),
                },
                validation={
                    "frame_sample": row.get("frame", 0),
                    "changed_field_count": len(changed_fields),
                },
                payload={field: row.get(field) for field in tracked_fields},
            )
        )
        previous = row
    return events


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
