from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from .catalog import ROOT
from .input_log import parse_input_log, resolve_path
from .provenance import display_path


SCHEMA_VERSION = 1
Predicate = Callable[[tuple[str, ...]], bool]


def shrink_input_log(
    *,
    input_log: str | Path,
    predicate: Predicate,
    out_log: str = "",
    root: Path = ROOT,
) -> dict[str, Any]:
    path = Path(input_log) if Path(input_log).is_absolute() else root / input_log
    errors: list[str] = []
    if not path.exists():
        errors.append(f"missing input log: {input_log}")
        return empty_report(input_log=input_log, path=path, root=root, errors=errors)

    events, parse_errors = parse_input_log(path)
    if parse_errors:
        errors.extend(parse_errors)
        return empty_report(input_log=input_log, path=path, root=root, errors=errors)
    lines = tuple(str(event["raw"]) for event in events)
    trace: list[dict[str, Any]] = []
    if not lines:
        errors.append("input log has no shrinkable events")
        return empty_report(input_log=input_log, path=path, root=root, errors=errors)
    if not predicate(lines):
        errors.append("baseline input log does not reproduce the predicate")
        return {
            **base_report(input_log=input_log, path=path, root=root),
            "valid": False,
            "errors": errors,
            "original_event_count": len(lines),
            "shrunk_event_count": len(lines),
            "original_lines": list(lines),
            "shrunk_lines": list(lines),
            "reduction_trace": trace,
            "out_log": write_output(lines, out_log=out_log, root=root),
        }

    shrunk = ddmin_lines(lines, predicate=predicate, trace=trace)
    out = write_output(shrunk, out_log=out_log, root=root)
    return {
        **base_report(input_log=input_log, path=path, root=root),
        "valid": True,
        "errors": [],
        "original_event_count": len(lines),
        "shrunk_event_count": len(shrunk),
        "removed_event_count": len(lines) - len(shrunk),
        "original_lines": list(lines),
        "shrunk_lines": list(shrunk),
        "reduction_trace": trace,
        "reduction_step_count": len(trace),
        "out_log": out,
    }


def ddmin_lines(lines: Sequence[str], *, predicate: Predicate, trace: list[dict[str, Any]]) -> tuple[str, ...]:
    return tuple(ddmin_items(lines, predicate=predicate, trace=trace))


def ddmin_items(
    items: Sequence[Any],
    *,
    predicate: Callable[[tuple[Any, ...]], bool],
    trace: list[dict[str, Any]],
) -> tuple[Any, ...]:
    current = tuple(items)
    granularity = 2
    trial = 0
    while len(current) >= 2:
        chunk_size = max(1, (len(current) + granularity - 1) // granularity)
        changed = False
        for start in range(0, len(current), chunk_size):
            end = min(len(current), start + chunk_size)
            candidate = current[:start] + current[end:]
            if not candidate:
                continue
            trial += 1
            accepted = bool(predicate(candidate))
            trace.append(
                {
                    "trial": trial,
                    "removed_start": start,
                    "removed_end": end,
                    "removed_count": end - start,
                    "candidate_event_count": len(candidate),
                    "accepted": accepted,
                }
            )
            if accepted:
                current = candidate
                granularity = max(2, granularity - 1)
                changed = True
                break
        if changed:
            continue
        if granularity >= len(current):
            break
        granularity = min(len(current), granularity * 2)
    return current


def write_output(lines: Sequence[str], *, out_log: str, root: Path) -> dict[str, Any]:
    if not out_log:
        return {"path": "", "written": False}
    path = resolve_path(out_log, root=root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return {"path": display_path(path, root=root), "written": True}


def base_report(*, input_log: str | Path, path: Path, root: Path) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "unified_debugger_shrink_input_log",
        "input_log": str(input_log),
        "input_path": display_path(path, root=root),
    }


def empty_report(*, input_log: str | Path, path: Path, root: Path, errors: list[str]) -> dict[str, Any]:
    return {
        **base_report(input_log=input_log, path=path, root=root),
        "valid": False,
        "errors": errors,
        "original_event_count": 0,
        "shrunk_event_count": 0,
        "original_lines": [],
        "shrunk_lines": [],
        "reduction_trace": [],
        "out_log": {"path": "", "written": False},
    }


def format_report(report: dict[str, Any]) -> str:
    lines = [
        "Input-log shrinker",
        (
            f"valid={str(report.get('valid')).lower()} "
            f"events={report.get('original_event_count', 0)}->{report.get('shrunk_event_count', 0)} "
            f"steps={report.get('reduction_step_count', 0)}"
        ),
    ]
    for error in report.get("errors", []):
        lines.append(f"error: {error}")
    out_log = report.get("out_log") if isinstance(report.get("out_log"), dict) else {}
    if out_log.get("written"):
        lines.append(f"shrunk_log={out_log.get('path', '')}")
    return "\n".join(lines)


def report_json(report: dict[str, Any]) -> str:
    return json.dumps(report, sort_keys=True)
