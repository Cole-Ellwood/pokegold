from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.trace import runtime as trace_runtime

from .catalog import ROOT
from .hardware_regression import PAN_DOCS_CASES, normalize_event_type
from .provenance import resolve_path


SUPPORTED_RECORDER_PROTOCOL = (
    "pyboy.hardware_event_recorder",
    "pyboy.mb.hardware_event_recorder",
)


def build_hardware_event_stream_report(
    *,
    execute: bool = False,
    rom_path: str = "pokegold.gbc",
    frames: int = 90,
    root: Path = ROOT,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    events: list[dict[str, Any]] = []
    recorder_available = False
    recorder_kind = ""
    executed_frames = 0
    rom = resolve_path(rom_path, root=root) if rom_path else root / "pokegold.gbc"
    if frames < 1:
        errors.append("--frames must be positive")
    if execute and not rom.exists():
        errors.append(f"missing ROM: {rom_path}")
    if execute and not errors:
        probe = execute_hardware_event_stream_probe(rom=rom, frames=frames)
        errors.extend(probe["errors"])
        warnings.extend(probe["warnings"])
        recorder_available = bool(probe["recorder_available"])
        recorder_kind = str(probe["recorder_kind"])
        executed_frames = int(probe["executed_frames"])
        events = [normalize_hardware_event(item) for item in probe["events"]]
    elif not execute:
        warnings.append("hardware event stream probe was planned only; rerun with --execute")

    non_mutating = recorder_kind == "non_mutating_event_recorder"
    proof_grade_event_stream = bool(execute and recorder_available and non_mutating and events)
    coverage = case_event_coverage(events)
    complete_coverage = [item for item in coverage if item.get("complete")]
    incomplete_coverage = [item for item in coverage if not item.get("complete")]
    hardware_event_observed = proof_grade_event_stream
    hardware_behavior_proven = proof_grade_event_stream and bool(complete_coverage)
    hardware_proof_status = (
        "case_hardware_proof"
        if hardware_behavior_proven
        else ("observed_runtime_not_case_complete" if hardware_event_observed else "not_proven")
    )
    return {
        "schema_version": 1,
        "kind": "unified_debugger_hardware_event_stream",
        "root": str(root),
        "valid": not errors,
        "executed": execute,
        "rom": display_path(rom, root=root),
        "frames": frames,
        "executed_frames": executed_frames,
        "recorder_available": recorder_available,
        "recorder_kind": recorder_kind,
        "supported_recorder_protocol": list(SUPPORTED_RECORDER_PROTOCOL),
        "proof_grade_event_stream": proof_grade_event_stream,
        "non_mutating_event_recorder": non_mutating,
        "hardware_behavior_proven": hardware_behavior_proven,
        "hardware_event_observed": hardware_event_observed,
        "hardware_proof_status": hardware_proof_status,
        "proof_status": "runtime_observed" if hardware_event_observed else "planned_only",
        "evidence_source": "non_mutating_event_recorder" if hardware_event_observed else "",
        "evidence_status": "non_mutating_event_recorder" if hardware_event_observed else "",
        "event_count": len(events),
        "events": events,
        "case_event_coverage": coverage,
        "case_event_coverage_count": len(coverage),
        "hardware_proven_case_count": len(complete_coverage),
        "hardware_proven_case_ids": [str(item.get("case_id", "")) for item in complete_coverage if item.get("case_id")],
        "incomplete_case_event_count": len(incomplete_coverage),
        "incomplete_case_event_ids": [str(item.get("case_id", "")) for item in incomplete_coverage if item.get("case_id")],
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "commands": ["python -m tools.debugger hardware-event-stream --execute"],
        "known_limits": [
            "Stock PyBoy does not expose a non-mutating hardware event recorder through the public API.",
            "Debugger hooks remain opcode-replacement breakpoints and are intentionally not converted into this event stream.",
            "This report is proof-grade only when an instrumented runtime exposes a non-mutating hardware event recorder.",
            "Observed hardware events are not case-complete hardware proof unless the matching Pan Docs case coverage is complete.",
        ],
    }


def execute_hardware_event_stream_probe(*, rom: Path, frames: int) -> dict[str, Any]:
    pyboy = None
    errors: list[str] = []
    warnings: list[str] = []
    events: list[dict[str, Any]] = []
    recorder_available = False
    recorder_kind = ""
    executed_frames = 0
    try:
        pyboy = trace_runtime.open_pyboy(
            rom,
            "PyBoy is required for hardware event stream probing. Import failed",
        )
        trace_runtime.disable_realtime(pyboy)
        recorder = hardware_event_recorder(pyboy)
        if recorder is None:
            warnings.append("no supported non-mutating hardware event recorder API found on PyBoy")
        else:
            recorder_available = True
            recorder_kind = recorder_kind_for(recorder)
            start_recorder(recorder)
            for _index in range(frames):
                pyboy.tick(1, False, False)
                executed_frames += 1
            events = recorder_events(recorder)
            stop_recorder(recorder)
    except SystemExit as exc:
        errors.append(str(exc))
    except Exception as exc:
        errors.append(f"hardware event stream probe failed: {exc}")
    finally:
        if pyboy is not None:
            try:
                pyboy.stop(save=False)
            except TypeError:
                pyboy.stop()
            except Exception:
                pass
    return {
        "errors": errors,
        "warnings": warnings,
        "events": events,
        "recorder_available": recorder_available,
        "recorder_kind": recorder_kind,
        "executed_frames": executed_frames,
    }


def hardware_event_recorder(pyboy: Any) -> Any | None:
    for owner in (pyboy, getattr(pyboy, "mb", None)):
        if owner is None:
            continue
        recorder = getattr(owner, "hardware_event_recorder", None)
        if callable(recorder):
            recorder = recorder()
        if recorder is not None:
            return recorder
    return None


def recorder_kind_for(recorder: Any) -> str:
    if bool(getattr(recorder, "non_mutating_event_recorder", False)):
        return "non_mutating_event_recorder"
    if bool(getattr(recorder, "non_mutating", False)):
        return "non_mutating_event_recorder"
    kind = str(getattr(recorder, "recorder_kind", "") or getattr(recorder, "kind", ""))
    if kind == "non_mutating_event_recorder":
        return kind
    return kind or "hardware_event_recorder"


def start_recorder(recorder: Any) -> None:
    for method_name in ("start", "begin"):
        method = getattr(recorder, method_name, None)
        if callable(method):
            method()
            return


def stop_recorder(recorder: Any) -> None:
    for method_name in ("stop", "end"):
        method = getattr(recorder, method_name, None)
        if callable(method):
            method()
            return


def recorder_events(recorder: Any) -> list[dict[str, Any]]:
    for method_name in ("drain_events", "get_events"):
        method = getattr(recorder, method_name, None)
        if callable(method):
            return dict_items(method())
    return dict_items(getattr(recorder, "events", []))


def normalize_hardware_event(event: dict[str, Any]) -> dict[str, Any]:
    event_type = normalize_event_type(
        str(
            event.get("hardware_event_type")
            or event.get("event_type")
            or event.get("type")
            or event.get("kind")
            or ""
        )
    )
    out = {key: event[key] for key in sorted(event) if key not in {"hardware_regression_case_ids", "case_ids"}}
    if event_type:
        out["event_type"] = event_type
    case_ids = set(string_items(event.get("hardware_regression_case_ids")))
    case_ids.update(string_items(event.get("hardware_regression_case_id")))
    case_ids.update(string_items(event.get("case_ids")))
    case_ids.update(string_items(event.get("case_id")))
    if event_type:
        case_ids.update(case_ids_for_event_type(event_type))
    if case_ids:
        out["hardware_regression_case_ids"] = sorted(case_ids)
    return out


def case_event_coverage(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for case in PAN_DOCS_CASES:
        required = [normalize_event_type(value) for value in string_items(case.get("required_event_types"))]
        observed = sorted(
            {
                normalize_event_type(str(event.get("event_type", "")))
                for event in events
                if str(case["id"]) in string_items(event.get("hardware_regression_case_ids"))
            }
        )
        if not observed:
            continue
        missing = [value for value in required if value not in observed]
        out.append(
            {
                "case_id": str(case["id"]),
                "observed_event_types": observed,
                "missing_event_types": missing,
                "complete": not missing,
            }
        )
    return out


def case_ids_for_event_type(event_type: str) -> set[str]:
    normalized = normalize_event_type(event_type)
    out: set[str] = set()
    for case in PAN_DOCS_CASES:
        required = {normalize_event_type(value) for value in string_items(case.get("required_event_types"))}
        if normalized in required:
            out.add(str(case["id"]))
    return out


def dict_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, tuple):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        return [value]
    return []


def string_items(value: Any) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item)]
    if value:
        return [str(value)]
    return []


def display_path(path: Path, *, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
