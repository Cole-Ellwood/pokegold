from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable, Iterable, Mapping, Sequence

from tools.trace import runtime as trace_runtime

from .catalog import ROOT
from .ingest import sha256_file
from .input_log import build_input_playback, play_inputs_for_frame
from .provenance import display_path, resolve_path
from .visual_snapshot import IO_REGISTERS, read_byte, read_memory_range, screen_frame_snapshot


SCHEMA_VERSION = 1
DEFAULT_BACKEND_ORDER = ("pyboy", "sameboy", "gambatte", "vba-m")
DEFAULT_CONFORMANCE_STORE = Path("audit") / "crossemu_conformance.jsonl"
DEFAULT_ROM = "pokegold.gbc"
CONFORMANCE_KIND = "unified_debugger_crossemu_conformance"
CONFORMANCE_REQUIRED_TEXT_FIELDS = (
    "backend",
    "status",
    "suite",
    "rom",
    "rom_sha256",
    "command",
    "observed_at",
    "proof_status",
)
CONFORMANCE_STATUS_VALUES = {"pass", "fail"}
CONFORMANCE_PROOF_STATUS_VALUES = {"runtime_observed", "failed"}

ModuleFinder = Callable[[str], Any]
CommandFinder = Callable[[str], str | None]
PyBoyFactory = Callable[[Path], Any]


@dataclass(frozen=True)
class BackendSpec:
    name: str
    display_name: str
    role: str
    python_modules: tuple[str, ...] = ()
    commands: tuple[str, ...] = ()
    install_steps: tuple[str, ...] = ()
    notes: str = ""


BACKENDS: dict[str, BackendSpec] = {
    "pyboy": BackendSpec(
        name="pyboy",
        display_name="PyBoy",
        role="canonical",
        python_modules=("pyboy",),
        commands=("pyboy",),
        install_steps=("python -m pip install pyboy",),
        notes="Canonical local automation backend; still not proof for VBA/VBA-M-only symptoms.",
    ),
    "sameboy": BackendSpec(
        name="sameboy",
        display_name="SameBoy",
        role="cross_backend",
        commands=("sameboy", "sameboy-headless", "SameBoy.exe"),
        install_steps=(
            "Install a SameBoy CLI/headless build and put the executable on PATH.",
            "Then run: python -m tools.debugger crossemu preflight --backends sameboy",
        ),
        notes="Preferred timing-sensitive cross-check once a headless binary is available.",
    ),
    "gambatte": BackendSpec(
        name="gambatte",
        display_name="gambatte",
        role="cross_backend",
        commands=("gambatte-speedrun", "gambatte", "gambatte_sdl"),
        install_steps=(
            "Install gambatte-speedrun or another scriptable gambatte build on PATH.",
            "Then run: python -m tools.debugger crossemu preflight --backends gambatte",
        ),
        notes="Useful as a second CPU/PPU implementation once conformance-gated.",
    ),
    "vba-m": BackendSpec(
        name="vba-m",
        display_name="VisualBoyAdvance-M (VBA-M)",
        role="cross_backend",
        commands=("visualboyadvance-m", "vbam", "vba-m", "VisualBoyAdvance-M.exe"),
        install_steps=(
            "Install VisualBoyAdvance-M with a CLI/headless entry point on PATH.",
            "Then run: python -m tools.debugger crossemu preflight --backends vba-m",
        ),
        notes="Targets the May 2026 user-reported VBA/VBA-M divergence class.",
    ),
}

BACKEND_ALIASES = {
    "vbam": "vba-m",
    "vba": "vba-m",
    "visualboyadvance-m": "vba-m",
    "visual-boy-advance-m": "vba-m",
}


def normalize_backend_name(name: str) -> str:
    key = name.strip().lower().replace("_", "-")
    return BACKEND_ALIASES.get(key, key)


def parse_backend_list(spec: str | Sequence[str] | None) -> tuple[str, ...]:
    if spec is None:
        return DEFAULT_BACKEND_ORDER
    parts: list[str] = []
    if isinstance(spec, str):
        raw_items = spec.replace(";", ",").split(",")
    else:
        raw_items = []
        for item in spec:
            raw_items.extend(str(item).replace(";", ",").split(","))
    for raw in raw_items:
        name = normalize_backend_name(raw)
        if name and name not in parts:
            parts.append(name)
    return tuple(parts or DEFAULT_BACKEND_ORDER)


def build_preflight_report(
    *,
    backends: str | Sequence[str] | None = None,
    conformance_store: str | Path = DEFAULT_CONFORMANCE_STORE,
    conformance_rows: Iterable[Mapping[str, Any]] | None = None,
    root: Path = ROOT,
    module_finder: ModuleFinder = importlib.util.find_spec,
    command_finder: CommandFinder = shutil.which,
) -> dict[str, Any]:
    requested = parse_backend_list(backends)
    errors = [f"unknown backend {name!r}" for name in requested if name not in BACKENDS]
    rows, row_errors = _conformance_rows(
        conformance_store=conformance_store,
        conformance_rows=conformance_rows,
        root=root,
    )
    errors.extend(row_errors)

    entries = [
        _discover_backend(
            BACKENDS[name],
            conformance_rows=rows,
            module_finder=module_finder,
            command_finder=command_finder,
        )
        for name in requested
        if name in BACKENDS
    ]
    by_name = {entry["name"]: entry for entry in entries}
    pyboy = by_name.get("pyboy")
    cross_backends = [entry for entry in entries if entry["role"] == "cross_backend"]
    available_cross = [entry for entry in cross_backends if entry["available"]]
    trusted_cross = [entry for entry in cross_backends if entry["trusted_for_differential"]]

    blocking_reasons: list[str] = []
    if pyboy is None:
        blocking_reasons.append("pyboy backend was not selected")
    elif not pyboy["available"]:
        blocking_reasons.append("pyboy backend is not available for canonical run")
    if not available_cross:
        blocking_reasons.append("no cross-emulator backend is installed")
    elif not trusted_cross:
        blocking_reasons.append("no conformance-passing cross-emulator backend is installed")

    return {
        "kind": "unified_debugger_crossemu_preflight",
        "schema_version": SCHEMA_VERSION,
        "valid": not errors,
        "requested_backends": list(requested),
        "available_count": sum(1 for entry in entries if entry["available"]),
        "cross_backend_available_count": len(available_cross),
        "trusted_cross_backend_count": len(trusted_cross),
        "ready_for_pyboy_run": bool(pyboy and pyboy["available"]),
        "ready_for_cross_backend_diff": bool(pyboy and pyboy["available"] and trusted_cross),
        "blocking_reasons": blocking_reasons,
        "backends": entries,
        "errors": errors,
        "conformance_store": str(_resolve_path(conformance_store, root=root)),
    }


def build_install_docs_report(
    *,
    backends: str | Sequence[str] | None = None,
    missing_only: bool = True,
    root: Path = ROOT,
    module_finder: ModuleFinder = importlib.util.find_spec,
    command_finder: CommandFinder = shutil.which,
) -> dict[str, Any]:
    preflight = build_preflight_report(
        backends=backends,
        conformance_rows=(),
        root=root,
        module_finder=module_finder,
        command_finder=command_finder,
    )
    recipes: list[dict[str, Any]] = []
    for entry in preflight["backends"]:
        if missing_only and entry["available"]:
            continue
        spec = BACKENDS[entry["name"]]
        recipes.append(
            {
                "name": spec.name,
                "display_name": spec.display_name,
                "available": entry["available"],
                "install_steps": list(spec.install_steps),
                "verify_command": (
                    f"python -m tools.debugger crossemu preflight --backends {spec.name}"
                ),
                "notes": spec.notes,
            }
        )
    return {
        "kind": "unified_debugger_crossemu_install_docs",
        "schema_version": SCHEMA_VERSION,
        "valid": preflight["valid"],
        "missing_only": missing_only,
        "recipes": recipes,
        "errors": list(preflight["errors"]),
    }


def write_json_report(path: str | Path, report: Mapping[str, Any]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return target


def build_run_report(
    *,
    backends: str | Sequence[str] | None = ("pyboy",),
    rom_path: str = DEFAULT_ROM,
    save_state: str = "",
    frames: int = 0,
    input_logs: Sequence[str] = (),
    root: Path = ROOT,
    module_finder: ModuleFinder = importlib.util.find_spec,
    command_finder: CommandFinder = shutil.which,
    pyboy_factory: PyBoyFactory | None = None,
) -> dict[str, Any]:
    requested = parse_backend_list(backends)
    rom = resolve_path(rom_path, root=root)
    save = resolve_path(save_state, root=root) if save_state else None
    errors = [f"unknown backend {name!r}" for name in requested if name not in BACKENDS]
    warnings: list[str] = []
    if frames < 0:
        errors.append("--frames must be non-negative")
    if not save_state:
        errors.append("--save-state is required for crossemu run")
    elif save is not None and not save.exists():
        errors.append(f"missing save-state: {save_state}")
    if not rom.exists():
        errors.append(f"missing ROM: {rom_path}")

    supported = [name for name in requested if name == "pyboy"]
    unsupported = [name for name in requested if name in BACKENDS and name != "pyboy"]
    if unsupported:
        errors.append(
            "crossemu run currently supports --backends pyboy only; "
            f"pending adapters: {', '.join(unsupported)}"
        )
    if not supported and not unsupported:
        errors.append("no runnable backend selected")
    elif not supported and unsupported:
        errors.append("no implemented backend selected")

    preflight = build_preflight_report(
        backends=requested,
        conformance_rows=(),
        root=root,
        module_finder=module_finder,
        command_finder=command_finder,
    )
    pyboy_entry = next(
        (entry for entry in preflight.get("backends", []) if entry.get("name") == "pyboy"),
        None,
    )
    if "pyboy" in supported and pyboy_entry and not pyboy_entry.get("available"):
        errors.append("pyboy backend is not available for crossemu run")

    input_playback = build_input_playback(tuple(input_logs), root=root, max_events=0)
    errors.extend(input_playback.get("errors", []))
    warnings.extend(input_playback.get("warnings", []))

    backend_results = [
        {
            "backend": name,
            "status": "planned_only",
            "proof_status": "planned_only",
            "blocking_reason": "backend adapter is not implemented in this slice",
        }
        for name in unsupported
    ]
    report: dict[str, Any] = {
        "kind": "unified_debugger_crossemu_run",
        "schema_version": SCHEMA_VERSION,
        "valid": not errors,
        "executed": False,
        "proof_status": "planned_only",
        "hardware_behavior_proven": False,
        "hardware_proof_boundary": (
            "PyBoy crossemu run captures emulator-observed memory/framebuffer state; "
            "cross-emulator or hardware agreement is not proven until another backend runs."
        ),
        "requested_backends": list(requested),
        "rom": display_path(rom, root=root),
        "rom_sha256": sha256_file(rom) if rom.exists() else "",
        "save_state": display_path(save, root=root) if save is not None else "",
        "frames": max(0, int(frames)),
        "input_logs": list(input_logs),
        "input_playback": input_playback,
        "backend_preflight": preflight,
        "backend_results": backend_results,
        "backend_result_count": len(backend_results),
        "snapshot_diff": diff_backend_snapshots(backend_results),
        "errors": errors,
        "warnings": warnings,
        "error_count": len(errors),
        "warning_count": len(warnings),
    }
    if errors:
        return report

    pyboy_result = execute_pyboy_run(
        rom=rom,
        save_state=save,
        frames=max(0, int(frames)),
        input_playback=input_playback,
        pyboy_factory=pyboy_factory,
    )
    backend_results.insert(0, pyboy_result)
    snapshot_diff = diff_backend_snapshots(backend_results)
    report.update(
        {
            "valid": not pyboy_result.get("errors"),
            "executed": True,
            "proof_status": pyboy_result.get("proof_status", "runtime_observed"),
            "backend_results": backend_results,
            "backend_result_count": len(backend_results),
            "snapshot_diff": snapshot_diff,
            "divergent": snapshot_diff.get("divergent", False),
            "divergence_count": snapshot_diff.get("divergence_count", 0),
            "errors": list(pyboy_result.get("errors", [])),
            "warnings": warnings,
        }
    )
    report["error_count"] = len(report["errors"])
    report["warning_count"] = len(report["warnings"])
    return report


def build_report_diff_report(
    *,
    reports: Sequence[str],
    root: Path = ROOT,
) -> dict[str, Any]:
    errors: list[str] = []
    report_entries: list[dict[str, Any]] = []
    backend_results: list[Mapping[str, Any]] = []
    for raw_path in reports:
        path = _resolve_path(raw_path, root=root)
        entry: dict[str, Any] = {
            "path": display_path(path, root=root),
            "loaded": False,
            "backend_result_count": 0,
            "errors": [],
        }
        if not path.exists():
            error = f"missing report: {raw_path}"
            entry["errors"].append(error)
            errors.append(error)
            report_entries.append(entry)
            continue
        try:
            decoded = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            error = f"{display_path(path, root=root)}: invalid JSON: {exc.msg}"
            entry["errors"].append(error)
            errors.append(error)
            report_entries.append(entry)
            continue
        if not isinstance(decoded, Mapping):
            error = f"{display_path(path, root=root)}: expected object report"
            entry["errors"].append(error)
            errors.append(error)
            report_entries.append(entry)
            continue
        if decoded.get("kind") != "unified_debugger_crossemu_run":
            error = f"{display_path(path, root=root)}: expected crossemu run report"
            entry["errors"].append(error)
            errors.append(error)
            report_entries.append(entry)
            continue

        results = [
            result
            for result in decoded.get("backend_results", [])
            if isinstance(result, Mapping)
        ]
        entry["loaded"] = True
        entry["backend_result_count"] = len(results)
        entry["runtime_backend_count"] = sum(
            1 for result in results if result.get("status") == "runtime_observed"
        )
        backend_results.extend(results)
        report_entries.append(entry)

    snapshot_diff = diff_backend_snapshots(backend_results)
    blocking_reasons: list[str] = []
    if snapshot_diff.get("runtime_backend_count", 0) < 2:
        blocking_reasons.append("need at least two runtime backend snapshots")
    return {
        "kind": "unified_debugger_crossemu_report_diff",
        "schema_version": SCHEMA_VERSION,
        "valid": not errors and not blocking_reasons,
        "report_count": len(reports),
        "reports": report_entries,
        "backend_result_count": len(backend_results),
        "snapshot_diff": snapshot_diff,
        "divergent": snapshot_diff.get("divergent", False),
        "divergence_count": snapshot_diff.get("divergence_count", 0),
        "blocking_reasons": blocking_reasons,
        "errors": errors,
        "error_count": len(errors),
    }


def diff_backend_snapshots(backend_results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = [
        result
        for result in backend_results
        if result.get("status") == "runtime_observed"
        and isinstance(result.get("snapshot"), Mapping)
    ]
    comparisons: list[dict[str, Any]] = []
    if len(observed) >= 2:
        left = observed[0]
        for right in observed[1:]:
            comparisons.append(compare_snapshot_pair(left, right))
    divergence_count = sum(
        int(item.get("difference_count", 0))
        for item in comparisons
    )
    if not comparisons:
        status = "not_enough_runtime_backends"
    elif divergence_count:
        status = "diverged"
    else:
        status = "matched"
    return {
        "kind": "unified_debugger_crossemu_snapshot_diff",
        "schema_version": SCHEMA_VERSION,
        "valid": True,
        "status": status,
        "proof_status": "runtime_observed" if comparisons else "planned_only",
        "runtime_backend_count": len(observed),
        "comparison_count": len(comparisons),
        "divergent": bool(divergence_count),
        "divergence_count": divergence_count,
        "comparisons": comparisons,
        "known_limits": [
            "Snapshot diffs compare emulator-observed digests from completed backend runs.",
            "A matching digest does not prove hardware accuracy; it only proves agreement among captured backend states.",
        ],
    }


def compare_snapshot_pair(
    left_result: Mapping[str, Any],
    right_result: Mapping[str, Any],
) -> dict[str, Any]:
    left_snapshot = dict(left_result.get("snapshot") or {})
    right_snapshot = dict(right_result.get("snapshot") or {})
    region_differences = compare_regions(
        left_snapshot.get("regions", []),
        right_snapshot.get("regions", []),
    )
    screen_difference = compare_screen_frame(
        left_snapshot.get("screen_frame"),
        right_snapshot.get("screen_frame"),
    )
    differences = list(region_differences)
    if screen_difference:
        differences.append(screen_difference)
    return {
        "left_backend": str(left_result.get("backend", "")),
        "right_backend": str(right_result.get("backend", "")),
        "difference_count": len(differences),
        "region_difference_count": len(region_differences),
        "screen_difference": screen_difference,
        "region_differences": region_differences,
    }


def compare_regions(left_regions: Any, right_regions: Any) -> list[dict[str, Any]]:
    left_by_name = {
        str(region.get("name")): region
        for region in left_regions
        if isinstance(region, Mapping) and region.get("name")
    }
    right_by_name = {
        str(region.get("name")): region
        for region in right_regions
        if isinstance(region, Mapping) and region.get("name")
    }
    differences: list[dict[str, Any]] = []
    for name in sorted(set(left_by_name) | set(right_by_name)):
        left = left_by_name.get(name)
        right = right_by_name.get(name)
        if left is None:
            differences.append({"kind": "region_missing_left", "region": name})
            continue
        if right is None:
            differences.append({"kind": "region_missing_right", "region": name})
            continue
        if left.get("sha256") != right.get("sha256"):
            differences.append(
                {
                    "kind": "region_sha256_mismatch",
                    "region": name,
                    "left_sha256": str(left.get("sha256", "")),
                    "right_sha256": str(right.get("sha256", "")),
                    "left_address": str(left.get("address", "")),
                    "right_address": str(right.get("address", "")),
                    "left_bank": str(left.get("bank", "")),
                    "right_bank": str(right.get("bank", "")),
                    "left_bank_read": str(left.get("bank_read", "")),
                    "right_bank_read": str(right.get("bank_read", "")),
                    "left_size": left.get("size", 0),
                    "right_size": right.get("size", 0),
                    "left_nonzero_count": left.get("nonzero_count", 0),
                    "right_nonzero_count": right.get("nonzero_count", 0),
                    "left_unique_byte_count": left.get("unique_byte_count", 0),
                    "right_unique_byte_count": right.get("unique_byte_count", 0),
                    "left_sample_size": left.get("sample_size", 0),
                    "right_sample_size": right.get("sample_size", 0),
                    "left_sample_hex": str(left.get("sample_hex", "")),
                    "right_sample_hex": str(right.get("sample_hex", "")),
                    "left_truncated": bool(left.get("truncated", False)),
                    "right_truncated": bool(right.get("truncated", False)),
                }
            )
    return differences


def compare_screen_frame(left_screen: Any, right_screen: Any) -> dict[str, Any]:
    if not isinstance(left_screen, Mapping) and not isinstance(right_screen, Mapping):
        return {}
    if not isinstance(left_screen, Mapping):
        return {"kind": "screen_frame_missing_left"}
    if not isinstance(right_screen, Mapping):
        return {"kind": "screen_frame_missing_right"}
    if left_screen.get("sha256") != right_screen.get("sha256"):
        return {
            "kind": "screen_frame_sha256_mismatch",
            "left_sha256": str(left_screen.get("sha256", "")),
            "right_sha256": str(right_screen.get("sha256", "")),
            "left_screen_source": str(left_screen.get("screen_source", "")),
            "right_screen_source": str(right_screen.get("screen_source", "")),
            "left_width": left_screen.get("width", 0),
            "right_width": right_screen.get("width", 0),
            "left_height": left_screen.get("height", 0),
            "right_height": right_screen.get("height", 0),
            "left_mode": str(left_screen.get("mode", "")),
            "right_mode": str(right_screen.get("mode", "")),
            "left_byte_count": left_screen.get("byte_count", 0),
            "right_byte_count": right_screen.get("byte_count", 0),
            "left_sample_size": left_screen.get("sample_size", 0),
            "right_sample_size": right_screen.get("sample_size", 0),
            "left_sample_hex": str(left_screen.get("sample_hex", "")),
            "right_sample_hex": str(right_screen.get("sample_hex", "")),
            "left_truncated": bool(left_screen.get("truncated", False)),
            "right_truncated": bool(right_screen.get("truncated", False)),
        }
    return {}


def execute_pyboy_run(
    *,
    rom: Path,
    save_state: Path | None,
    frames: int,
    input_playback: Mapping[str, Any],
    pyboy_factory: PyBoyFactory | None = None,
) -> dict[str, Any]:
    pyboy: Any | None = None
    errors: list[str] = []
    played_inputs: list[dict[str, Any]] = []
    stopped = False
    tick_count = 0
    try:
        pyboy = (
            pyboy_factory(rom)
            if pyboy_factory is not None
            else trace_runtime.open_pyboy(
                rom,
                "PyBoy is required for crossemu run. Import failed",
            )
        )
        trace_runtime.disable_realtime(pyboy)
        if save_state is not None:
            with save_state.open("rb") as fh:
                pyboy.load_state(fh)
        for frame in range(max(0, int(frames))):
            played_inputs.extend(play_inputs_for_frame(pyboy, dict(input_playback), frame))
            running = pyboy.tick(1, False, False)
            tick_count += 1
            if running is False:
                stopped = True
                break
        snapshot = pyboy_runtime_snapshot(pyboy, frame=frames)
    except SystemExit as exc:
        errors.append(f"pyboy run failed: SystemExit: {exc.code}")
        snapshot = {}
    except Exception as exc:  # noqa: BLE001 - execution report carries backend failure.
        errors.append(f"pyboy run failed: {type(exc).__name__}: {exc}")
        snapshot = {}
    finally:
        if pyboy is not None:
            try:
                pyboy.stop(save=False)
            except TypeError:
                pyboy.stop()
            except Exception:
                pass
    return {
        "backend": "pyboy",
        "status": "runtime_observed" if not errors else "failed",
        "proof_status": "runtime_observed" if not errors else "planned_only",
        "executed_frame_count": tick_count if not errors else 0,
        "stopped": stopped,
        "played_inputs": played_inputs,
        "played_input_count": len(played_inputs),
        "snapshot": snapshot,
        "errors": errors,
    }


def pyboy_runtime_snapshot(pyboy: Any, *, frame: int, max_sample_bytes: int = 512) -> dict[str, Any]:
    svbk = read_byte(pyboy, 0xFF70) & 0x07
    wramx_bank = svbk or 1
    regions = [
        memory_region_snapshot(pyboy, name="vram0", address=0x8000, size=0x2000, bank=0, max_sample_bytes=max_sample_bytes),
        memory_region_snapshot(pyboy, name="vram1", address=0x8000, size=0x2000, bank=1, max_sample_bytes=max_sample_bytes),
        memory_region_snapshot(pyboy, name="wram0", address=0xC000, size=0x1000, bank=None, max_sample_bytes=max_sample_bytes),
        memory_region_snapshot(pyboy, name="wramx", address=0xD000, size=0x1000, bank=wramx_bank, max_sample_bytes=max_sample_bytes),
        memory_region_snapshot(pyboy, name="oam", address=0xFE00, size=0x00A0, bank=None, max_sample_bytes=max_sample_bytes),
        memory_region_snapshot(pyboy, name="io", address=0xFF00, size=0x0080, bank=None, max_sample_bytes=max_sample_bytes),
    ]
    io_registers = {
        name: f"{read_byte(pyboy, address):02X}"
        for name, address in IO_REGISTERS.items()
    }
    frame_snapshot = screen_frame_snapshot(pyboy, frame=frame, max_bytes=max_sample_bytes)
    return {
        "kind": "pyboy_runtime_snapshot",
        "schema_version": SCHEMA_VERSION,
        "region_count": len(regions),
        "regions": regions,
        "io_registers": io_registers,
        "screen_frame_count": 1 if frame_snapshot else 0,
        "screen_frame": frame_snapshot,
    }


def memory_region_snapshot(
    pyboy: Any,
    *,
    name: str,
    address: int,
    size: int,
    bank: int | None,
    max_sample_bytes: int,
) -> dict[str, Any]:
    values, bank_read = read_memory_range(pyboy, address=address, size=size, bank=bank)
    data = bytes(values)
    sample = data[:max(0, int(max_sample_bytes))]
    return {
        "name": name,
        "address": f"{address & 0xFFFF:04X}",
        "bank": "" if bank is None else f"{bank & 0xFF:02X}",
        "bank_read": bank_read,
        "size": size,
        "sha256": hashlib.sha256(data).hexdigest(),
        "nonzero_count": sum(1 for value in values if value),
        "unique_byte_count": len(set(values)),
        "sample_size": len(sample),
        "sample_hex": sample.hex().upper(),
        "truncated": len(sample) < len(data),
    }


def run_self_test() -> dict[str, Any]:
    class FakeMemory:
        def __getitem__(self, key: Any) -> int:
            if isinstance(key, tuple):
                bank, address = key
                return (int(bank) * 17 + int(address)) & 0xFF
            if int(key) == 0xFF70:
                return 2
            return int(key) & 0xFF

    class FakeScreen:
        def ndarray(self) -> bytes:
            return bytes(range(16))

    class FakePyBoy:
        def __init__(self) -> None:
            self.memory = FakeMemory()
            self.screen = FakeScreen()

        def load_state(self, _fh: Any) -> None:
            return None

        def button(self, _name: str, delay: int = 1) -> None:
            return None

        def tick(self, _count: int, _render: bool, _sound: bool) -> bool:
            return True

        def stop(self, save: bool = False) -> None:
            return None

    def fake_module_finder(name: str) -> object | None:
        return object() if name == "pyboy" else None

    def fake_command_finder(name: str) -> str | None:
        return "C:/tools/sameboy.exe" if name == "sameboy-headless" else None

    def conformance_row(backend: str, status: str) -> dict[str, Any]:
        return {
            "kind": CONFORMANCE_KIND,
            "schema_version": SCHEMA_VERSION,
            "backend": backend,
            "status": status,
            "suite": "selftest",
            "rom": "selftest.gb",
            "rom_sha256": "0" * 64,
            "command": "python -m tools.debugger selftest --component crossemu",
            "observed_at": "selftest",
            "proof_status": "runtime_observed",
        }

    report = build_preflight_report(
        backends=("pyboy", "sameboy", "gambatte"),
        conformance_rows=(
            conformance_row("sameboy", "pass"),
            conformance_row("gambatte", "fail"),
        ),
        module_finder=fake_module_finder,
        command_finder=fake_command_finder,
    )
    with TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        (tmp_root / "unit.gb").write_bytes(b"rom")
        (tmp_root / "unit.state").write_bytes(b"state")
        (tmp_root / "unit.inputs").write_text("A\nWAIT 1\n", encoding="utf-8")
        run = build_run_report(
            backends=("pyboy",),
            rom_path="unit.gb",
            save_state="unit.state",
            frames=2,
            input_logs=("unit.inputs",),
            root=tmp_root,
            module_finder=fake_module_finder,
            command_finder=fake_command_finder,
            pyboy_factory=lambda _rom: FakePyBoy(),
        )
    pyboy_result = run["backend_results"][0]
    sameboy_result = json.loads(json.dumps(pyboy_result))
    sameboy_result["backend"] = "sameboy"
    sameboy_result["snapshot"]["regions"][0]["sha256"] = "different"
    snapshot_diff = diff_backend_snapshots((pyboy_result, sameboy_result))
    return {
        "kind": "unified_debugger_crossemu_selftest",
        "schema_version": SCHEMA_VERSION,
        "passed": bool(
            report["valid"]
            and report["ready_for_cross_backend_diff"]
            and run["valid"]
            and run["executed"]
            and snapshot_diff["divergent"]
        ),
        "preflight": report,
        "run": run,
        "snapshot_diff": snapshot_diff,
    }


def _discover_backend(
    spec: BackendSpec,
    *,
    conformance_rows: Sequence[Mapping[str, Any]],
    module_finder: ModuleFinder,
    command_finder: CommandFinder,
) -> dict[str, Any]:
    probes: list[dict[str, Any]] = []
    availability_proof = ""
    for module in spec.python_modules:
        found = module_finder(module)
        probe = {
            "kind": "python_module",
            "name": module,
            "available": found is not None,
            "path": _module_origin(found),
        }
        probes.append(probe)
        if found is not None and not availability_proof:
            availability_proof = f"python_module:{module}"
    for command in spec.commands:
        found_path = command_finder(command)
        probe = {
            "kind": "command",
            "name": command,
            "available": bool(found_path),
            "path": str(found_path or ""),
        }
        probes.append(probe)
        if found_path and not availability_proof:
            availability_proof = f"command:{command}"

    conformance_status = _latest_conformance_status(spec.name, conformance_rows)
    available = bool(availability_proof)
    return {
        "name": spec.name,
        "display_name": spec.display_name,
        "role": spec.role,
        "status": "available" if available else "missing",
        "available": available,
        "availability_proof": availability_proof,
        "missing_reason": "" if available else "no Python module or executable found",
        "discovery": probes,
        "conformance_status": conformance_status,
        "trusted_for_differential": available and conformance_status == "pass",
        "install_hint": spec.install_steps[0] if spec.install_steps else "",
        "notes": spec.notes,
    }


def _latest_conformance_status(backend: str, rows: Sequence[Mapping[str, Any]]) -> str:
    latest = "missing"
    for row in rows:
        if normalize_backend_name(str(row.get("backend", ""))) != backend:
            continue
        status = str(
            row.get("status")
            or row.get("result")
            or row.get("outcome")
            or ""
        ).strip().lower()
        if status in {"pass", "passed", "ok"}:
            latest = "pass"
        elif status in {"fail", "failed", "error"}:
            latest = "fail"
        else:
            latest = "unknown"
    return latest


def validate_conformance_row(row: Mapping[str, Any], *, source: str) -> list[str]:
    errors: list[str] = []
    if row.get("kind") != CONFORMANCE_KIND:
        errors.append(f"{source}: kind must be {CONFORMANCE_KIND!r}")
    if row.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"{source}: schema_version must be {SCHEMA_VERSION}")
    for field in CONFORMANCE_REQUIRED_TEXT_FIELDS:
        value = row.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{source}: {field} must be a non-empty string")

    backend = normalize_backend_name(str(row.get("backend", "")))
    if backend not in BACKENDS:
        errors.append(f"{source}: unknown backend {row.get('backend')!r}")

    status = str(row.get("status", "")).strip().lower()
    if status and status not in CONFORMANCE_STATUS_VALUES:
        errors.append(f"{source}: status must be one of {sorted(CONFORMANCE_STATUS_VALUES)}")

    proof_status = str(row.get("proof_status", "")).strip().lower()
    if proof_status and proof_status not in CONFORMANCE_PROOF_STATUS_VALUES:
        errors.append(
            f"{source}: proof_status must be one of {sorted(CONFORMANCE_PROOF_STATUS_VALUES)}"
        )
    if status == "pass" and proof_status and proof_status != "runtime_observed":
        errors.append(f"{source}: pass rows must have proof_status='runtime_observed'")

    rom_sha256 = str(row.get("rom_sha256", "")).strip()
    if rom_sha256 and (
        len(rom_sha256) != 64 or any(ch not in "0123456789abcdefABCDEF" for ch in rom_sha256)
    ):
        errors.append(f"{source}: rom_sha256 must be 64 hex characters")
    return errors


def _conformance_rows(
    *,
    conformance_store: str | Path,
    conformance_rows: Iterable[Mapping[str, Any]] | None,
    root: Path,
) -> tuple[list[Mapping[str, Any]], list[str]]:
    if conformance_rows is not None:
        rows: list[Mapping[str, Any]] = []
        errors: list[str] = []
        for index, row in enumerate(conformance_rows, start=1):
            row_errors = validate_conformance_row(
                row,
                source=f"provided conformance row {index}",
            )
            if row_errors:
                errors.extend(row_errors)
                continue
            rows.append(row)
        return rows, errors
    path = _resolve_path(conformance_store, root=root)
    if not path.exists():
        return [], []
    rows: list[Mapping[str, Any]] = []
    errors: list[str] = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"{path}:{lineno}: invalid JSON: {exc.msg}")
            continue
        if not isinstance(decoded, dict):
            errors.append(f"{path}:{lineno}: expected object row")
            continue
        row_errors = validate_conformance_row(decoded, source=f"{path}:{lineno}")
        if row_errors:
            errors.extend(row_errors)
            continue
        rows.append(decoded)
    return rows, errors


def _resolve_path(path: str | Path, *, root: Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else root / candidate


def _module_origin(candidate: Any) -> str:
    origin = getattr(candidate, "origin", "")
    return str(origin or "")


def format_preflight(report: Mapping[str, Any]) -> str:
    status = "PASS" if report.get("valid") else "FAIL"
    lines = [f"crossemu preflight: {status}"]
    for entry in report.get("backends", []):
        proof = entry.get("availability_proof") or entry.get("missing_reason") or "unknown"
        lines.append(f"  {entry['name']}: {entry['status']} ({proof})")
        lines.append(f"    conformance: {entry.get('conformance_status', 'missing')}")
    lines.append(f"ready_for_pyboy_run: {_yes_no(report.get('ready_for_pyboy_run'))}")
    lines.append(
        f"ready_for_cross_backend_diff: {_yes_no(report.get('ready_for_cross_backend_diff'))}"
    )
    blocking = report.get("blocking_reasons") or ()
    if blocking:
        lines.append("blocking_reasons:")
        lines.extend(f"  - {reason}" for reason in blocking)
    errors = report.get("errors") or ()
    if errors:
        lines.append("errors:")
        lines.extend(f"  - {error}" for error in errors)
    return "\n".join(lines)


def format_install_docs(report: Mapping[str, Any]) -> str:
    status = "PASS" if report.get("valid") else "FAIL"
    lines = [f"crossemu install-docs: {status}"]
    recipes = report.get("recipes") or ()
    if not recipes:
        lines.append("all requested backends are currently discoverable")
    for recipe in recipes:
        lines.append(f"{recipe['name']} ({recipe['display_name']}):")
        for step in recipe.get("install_steps", []):
            lines.append(f"  - {step}")
        lines.append(f"  verify: {recipe['verify_command']}")
    errors = report.get("errors") or ()
    if errors:
        lines.append("errors:")
        lines.extend(f"  - {error}" for error in errors)
    return "\n".join(lines)


def format_run(report: Mapping[str, Any]) -> str:
    status = "PASS" if report.get("valid") else "FAIL"
    lines = [f"crossemu run: {status}"]
    lines.append(f"proof_status: {report.get('proof_status', '')}")
    lines.append(f"backends: {', '.join(report.get('requested_backends', []))}")
    lines.append(f"frames: {report.get('frames', 0)}")
    for result in report.get("backend_results", []):
        line = (
            f"  {result.get('backend')}: {result.get('status')} "
            f"proof={result.get('proof_status')}"
        )
        if result.get("played_input_count"):
            line += f" inputs={result.get('played_input_count')}"
        lines.append(line)
        snapshot = result.get("snapshot") if isinstance(result, Mapping) else {}
        if isinstance(snapshot, Mapping) and snapshot:
            lines.append(
                f"    regions={snapshot.get('region_count', 0)} "
                f"screen_frames={snapshot.get('screen_frame_count', 0)}"
            )
        if result.get("blocking_reason"):
            lines.append(f"    blocked: {result.get('blocking_reason')}")
    snapshot_diff = report.get("snapshot_diff")
    if isinstance(snapshot_diff, Mapping):
        lines.append(
            "snapshot_diff: "
            f"{snapshot_diff.get('status')} "
            f"comparisons={snapshot_diff.get('comparison_count', 0)} "
            f"divergences={snapshot_diff.get('divergence_count', 0)}"
        )
    for warning in report.get("warnings", []):
        lines.append(f"warning: {warning}")
    for error in report.get("errors", []):
        lines.append(f"error: {error}")
    return "\n".join(lines)


def format_report_diff(report: Mapping[str, Any]) -> str:
    status = "PASS" if report.get("valid") else "FAIL"
    lines = [f"crossemu diff: {status}"]
    lines.append(f"reports: {report.get('report_count', 0)}")
    for entry in report.get("reports", []):
        loaded = "loaded" if entry.get("loaded") else "not-loaded"
        lines.append(
            f"  {entry.get('path')}: {loaded} "
            f"backend_results={entry.get('backend_result_count', 0)} "
            f"runtime={entry.get('runtime_backend_count', 0)}"
        )
    snapshot_diff = report.get("snapshot_diff")
    if isinstance(snapshot_diff, Mapping):
        lines.append(
            "snapshot_diff: "
            f"{snapshot_diff.get('status')} "
            f"comparisons={snapshot_diff.get('comparison_count', 0)} "
            f"divergences={snapshot_diff.get('divergence_count', 0)}"
        )
        for comparison in snapshot_diff.get("comparisons", []):
            lines.append(
                f"  {comparison.get('left_backend')} vs {comparison.get('right_backend')}: "
                f"differences={comparison.get('difference_count', 0)}"
            )
    for reason in report.get("blocking_reasons", []):
        lines.append(f"blocked: {reason}")
    for error in report.get("errors", []):
        lines.append(f"error: {error}")
    return "\n".join(lines)


def _yes_no(value: Any) -> str:
    return "yes" if value else "no"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.debugger crossemu",
        description="Cross-emulator differential preflight and install guidance.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    preflight = sub.add_parser(
        "preflight",
        help="Discover emulator backends and report whether cross-emulator diffing is gated.",
    )
    preflight.add_argument(
        "--backends",
        default=",".join(DEFAULT_BACKEND_ORDER),
        help="Comma-separated backend list, default: pyboy,sameboy,gambatte,vba-m.",
    )
    preflight.add_argument(
        "--conformance-store",
        default=str(DEFAULT_CONFORMANCE_STORE),
        help="JSONL conformance result store used to mark cross backends trusted.",
    )
    preflight.add_argument("--json", action="store_true")
    preflight.add_argument("--json-out", default="", help="write structured JSON to a file")
    preflight.set_defaults(func=cmd_preflight)

    install_docs = sub.add_parser(
        "install-docs",
        help="Print install/verify recipes for missing cross-emulator backends.",
    )
    install_docs.add_argument(
        "--backends",
        default=",".join(DEFAULT_BACKEND_ORDER),
        help="Comma-separated backend list, default: pyboy,sameboy,gambatte,vba-m.",
    )
    install_docs.add_argument(
        "--all",
        action="store_true",
        help="Show recipes for all requested backends, not just missing ones.",
    )
    install_docs.add_argument("--json", action="store_true")
    install_docs.add_argument("--json-out", default="", help="write structured JSON to a file")
    install_docs.set_defaults(func=cmd_install_docs)

    run = sub.add_parser(
        "run",
        help="Run the implemented PyBoy backend and capture a structured snapshot.",
    )
    run.add_argument(
        "--backends",
        default="pyboy",
        help="Comma-separated backend list. This slice implements pyboy only.",
    )
    run.add_argument("--rom", default=DEFAULT_ROM)
    run.add_argument("--save-state", required=True)
    run.add_argument("--frames", type=int, default=0)
    run.add_argument(
        "--inputs",
        action="append",
        default=[],
        help="Supported debugger text input log. Repeat for multiple logs.",
    )
    run.add_argument("--json", action="store_true")
    run.add_argument("--json-out", default="", help="write structured JSON to a file")
    run.set_defaults(func=cmd_run)

    diff = sub.add_parser(
        "diff",
        help="Diff saved crossemu JSON run reports without rerunning emulators.",
    )
    diff.add_argument(
        "--reports",
        nargs="+",
        required=True,
        help="One or more crossemu run JSON reports produced with --json-out.",
    )
    diff.add_argument("--json", action="store_true")
    diff.add_argument("--json-out", default="", help="write structured JSON to a file")
    diff.set_defaults(func=cmd_diff)
    return parser


def cmd_preflight(args: argparse.Namespace) -> int:
    report = build_preflight_report(
        backends=args.backends,
        conformance_store=args.conformance_store,
    )
    if args.json_out:
        write_json_report(args.json_out, report)
        return 0 if report["valid"] else 1
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(format_preflight(report))
    return 0 if report["valid"] else 1


def cmd_install_docs(args: argparse.Namespace) -> int:
    report = build_install_docs_report(
        backends=args.backends,
        missing_only=not args.all,
    )
    if args.json_out:
        write_json_report(args.json_out, report)
        return 0 if report["valid"] else 1
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(format_install_docs(report))
    return 0 if report["valid"] else 1


def cmd_run(args: argparse.Namespace) -> int:
    report = build_run_report(
        backends=args.backends,
        rom_path=args.rom,
        save_state=args.save_state,
        frames=args.frames,
        input_logs=tuple(args.inputs),
    )
    if args.json_out:
        write_json_report(args.json_out, report)
        return 0 if report["valid"] else 1
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(format_run(report))
    return 0 if report["valid"] else 1


def cmd_diff(args: argparse.Namespace) -> int:
    report = build_report_diff_report(reports=tuple(args.reports))
    if args.json_out:
        write_json_report(args.json_out, report)
        return 0 if report["valid"] else 1
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(format_report_diff(report))
    return 0 if report["valid"] else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
