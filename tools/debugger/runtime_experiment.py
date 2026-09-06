"""Replay a snapshot with observed, preconditioned register interventions.

This supplies evidence for a hypothesis; an intervention that changes the output
does not by itself prove a root cause. Each call starts a fresh emulator, loads
the same snapshot, and closes without saving. ROM/source/state files are read-only.
"""
from __future__ import annotations

import sys
import json
from pathlib import Path
from typing import Any

from tools.trace import runtime as trace_runtime

from .catalog import ROOT
from .provenance import parse_symbol_table, resolve_path
from .report_envelope import replay_state_basis, sha256_file
from .runtime_watch import build_watch_spec, bytes_hex, read_watch_bytes, register_snapshot


def run_runtime_experiment(
    *,
    rom_path: str,
    symbols_path: str,
    save_state: str,
    frames: int,
    observe: tuple[str, ...],
    watch_symbols: tuple[str, ...],
    interventions: tuple[dict[str, Any], ...],
    root: Path = ROOT,
) -> dict[str, Any]:
    """Observe ROM symbols (optionally +offset) and apply each intervention once.

    frames must be a positive integer. An intervention supplies at, register,
    expected, value. Only the byte registers A/B/C/D/E/H/L are supported here.
    Resolve all targets and validate all arguments before opening the emulator.
    At a checkpoint, check every expected register before applying any changes
    there. A mismatch, unreached target, or unapplied intervention invalidates the
    trial. Experiments at different checkpoints are not a rollback transaction.
    """
    rom = resolve_path(rom_path, root=root)
    symbols = resolve_path(symbols_path, root=root)
    state = resolve_path(save_state, root=root)
    errors: list[str] = []
    if type(frames) is not int or frames <= 0:
        errors.append("frames must be a positive integer")
    for name, path in (("ROM", rom), ("symbols", symbols), ("save state", state)):
        if not path.is_file():
            errors.append(f"missing {name}: {path}")
    table = parse_symbol_table(symbols) if symbols.is_file() else {}
    targets: dict[str, tuple[int, int]] = {}

    def resolve_target(text):
        if not isinstance(text, str) or not text:
            errors.append("checkpoint must be a symbol or symbol+offset")
            return
        if text in targets:
            return
        symbol, separator, offset_text = text.partition("+")
        entry = table.get(symbol)
        if entry is None:
            errors.append(f"unknown checkpoint symbol: {text}")
            return
        try:
            offset = int(offset_text, 0) if separator else 0
        except ValueError:
            errors.append(f"invalid checkpoint offset: {text}")
            return
        address, bank = int(entry["address"]) + offset, int(entry["bank"])
        if (offset < 0 or not 0 <= address < 0x8000
                or address // 0x4000 != int(entry["address"]) // 0x4000
                or (bank == 0) != (address < 0x4000)
                or rom.is_file() and bank * 0x4000 >= rom.stat().st_size):
            errors.append(f"checkpoint outside its ROM bank: {text}")
            return
        targets[text] = (bank, address)

    for target in observe:
        resolve_target(target)
    patches = []
    assigned = set()
    for item in interventions:
        if not isinstance(item, dict):
            errors.append("intervention must be an object")
            continue
        patch = {**item, "applied": False}
        patches.append(patch)
        resolve_target(item.get("at"))
        register = item.get("register")
        if not isinstance(register, str) or register not in {"A", "B", "C", "D", "E", "H", "L"}:
            errors.append("intervention register must be A/B/C/D/E/H/L")
        else:
            target = targets.get(item.get("at")) if isinstance(item.get("at"), str) else None
            if target is not None:
                key = (*target, register)
                if key in assigned:
                    errors.append(f"duplicate intervention for {item['at']} {register}")
                assigned.add(key)
        for key in ("expected", "value"):
            if type(item.get(key)) is not int or not 0 <= item[key] <= 255:
                errors.append(f"intervention {key} must be an integer byte")

    watches = [build_watch_spec(name, table, symbols_path=symbols, root=root) for name in watch_symbols]
    for watch in watches:
        if not watch["found"]:
            errors.append(f"unknown watch symbol: {watch['name']}")
    report = {
        "schema_version": 1, "kind": "unified_debugger_runtime_experiment",
        "root": str(root.resolve()), "rom_path": str(rom_path), "symbols_path": str(symbols_path),
        "save_state": str(save_state), "observe": list(observe), "watch_symbols": list(watch_symbols),
        "valid": False, "executed": False, "errors": errors,
        "rom_sha256": sha256_file(rom), "symbols_sha256": sha256_file(symbols),
        "initial_state_sha256": sha256_file(state), "frames": frames,
        "state_basis": replay_state_basis(state, frames),
        "events": [], "interventions": patches, "initial": {}, "final": {},
        "known_limits": [
            "A controlled register intervention tests a hypothesis; output restoration alone is not root-cause proof.",
            "Only the first hit at each intervention checkpoint is changed; no fresh-game reachability claim.",
        ],
    }
    if errors:
        return report

    pyboy = None
    hooked = set()
    hit = set()
    try:
        pyboy = trace_runtime.open_pyboy(rom, "PyBoy is required for runtime experiments")
        trace_runtime.disable_realtime(pyboy)
        backend = type(pyboy).__module__
        report["backend"] = f"{backend}.{type(pyboy).__name__}"
        report["backend_sha256"] = sha256_file(getattr(sys.modules.get(backend), "__file__", None))
        with state.open("rb") as handle:
            pyboy.load_state(handle)

        def snapshot():
            return {
                "registers": register_snapshot(pyboy),
                "watch_values": {watch["name"]: bytes_hex(read_watch_bytes(pyboy, watch)) for watch in watches},
            }

        def callback_for(point):
            names = [name for name, resolved in targets.items() if resolved == point]
            changes = [patch for patch in patches if patch["at"] in names]

            def callback(_context):
                before = snapshot()
                pending = [patch for patch in changes if not patch["applied"]]
                mismatched = [patch for patch in pending
                              if before["registers"].get(f"register_{patch['register'].lower()}")
                              != f"{patch['expected']:02X}"]
                for patch in mismatched:
                    errors.append(f"intervention preimage mismatch: {patch['at']} {patch['register']}")
                if not errors:
                    for patch in pending:
                        register, value = patch["register"], patch["value"]
                        if register in {"H", "L"} and hasattr(pyboy.register_file, "HL"):
                            pair = int(pyboy.register_file.HL)
                            pyboy.register_file.HL = ((pair & 0xFF) | (value << 8)) if register == "H" else ((pair & 0xFF00) | value)
                        else:
                            setattr(pyboy.register_file, register, value)
                        patch["applied"] = True
                hit.update(names)
                report["events"].append({
                    "seq": len(report["events"]), "targets": names,
                    "bank": point[0], "pc": point[1], **before,
                    "after_registers": register_snapshot(pyboy),
                })
            return callback

        for point in dict.fromkeys(targets.values()):
            pyboy.hook_register(*point, callback_for(point), None)
            hooked.add(point)
        report["initial"] = snapshot()
        report["executed"] = True
        pyboy.tick(frames, False, False)
        report["final"] = snapshot()
        errors.extend(f"checkpoint not reached: {name}" for name in targets if name not in hit)
        errors.extend(f"intervention not applied: {patch['at']} {patch['register']}"
                      for patch in patches if not patch["applied"])
    except Exception as exc:
        errors.append(f"runtime experiment failed: {exc}")
    finally:
        if pyboy is not None:
            for point in hooked:
                try:
                    pyboy.hook_deregister(*point)
                except Exception as exc:
                    errors.append(f"hook cleanup failed: {exc}")
            pyboy.stop(save=False)
    report["valid"] = not errors
    return report


def replay_experiment_report(path: Path) -> dict[str, Any]:
    """Revalidate one recorded experiment, not its intended-behavior contract."""
    recorded = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(recorded, dict) or recorded.get("kind") != "unified_debugger_runtime_experiment"
            or recorded.get("valid") is not True or recorded.get("executed") is not True):
        raise ValueError("a valid executed runtime experiment report is required")
    root = Path(recorded["root"])
    for name, key in (("rom_path", "rom_sha256"), ("symbols_path", "symbols_sha256"),
                      ("save_state", "initial_state_sha256")):
        if not recorded.get(key) or sha256_file(resolve_path(recorded[name], root=root)) != recorded[key]:
            raise ValueError(f"stale experiment {name}")
    state = resolve_path(recorded["save_state"], root=root)
    if recorded.get("state_basis") != replay_state_basis(state, recorded["frames"]):
        raise ValueError("stale experiment state or input schedule")
    backend_class = trace_runtime.load_pyboy("PyBoy is required to replay this experiment")
    backend = f"{backend_class.__module__}.{backend_class.__name__}"
    backend_file = getattr(sys.modules.get(backend_class.__module__), "__file__", None)
    if recorded.get("backend") != backend or recorded.get("backend_sha256") != sha256_file(backend_file):
        raise ValueError("experiment backend differs from its recording")
    result = run_runtime_experiment(
        rom_path=recorded["rom_path"], symbols_path=recorded["symbols_path"], save_state=recorded["save_state"],
        frames=recorded["frames"], observe=tuple(recorded["observe"]), watch_symbols=tuple(recorded["watch_symbols"]),
        interventions=tuple({key: patch[key] for key in ("at", "register", "expected", "value")}
                            for patch in recorded["interventions"]), root=root,
    )
    for key in ("initial", "events", "final"):
        if result.get(key) != recorded.get(key):
            result["errors"].append(f"replayed {key} differs from recording")
            result["valid"] = False
    return result
