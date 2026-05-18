from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .catalog import ROOT


BUTTON_ALIASES = {
    "A": "a",
    "B": "b",
    "START": "start",
    "SELECT": "select",
    "UP": "up",
    "DOWN": "down",
    "LEFT": "left",
    "RIGHT": "right",
}
WAIT_RE = re.compile(r"^(?:wait|frame|frames)\s*[:=]?\s*(?P<frames>\d+)$", re.IGNORECASE)


def build_input_playback(
    input_logs: tuple[str, ...],
    *,
    root: Path = ROOT,
    max_events: int = 200,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    logs: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    frame = 0
    for raw_path in input_logs:
        path = resolve_path(raw_path, root=root)
        log = {
            "path": display_path(path, root=root),
            "input_path": raw_path,
            "exists": path.exists(),
            "event_count": 0,
            "button_event_count": 0,
            "total_frames": 0,
            "errors": [],
        }
        if not path.exists():
            message = f"input log path does not exist: {raw_path}"
            errors.append(message)
            log["errors"].append(message)
            logs.append(log)
            continue
        start_frame = frame
        parsed_events, parsed_errors = parse_input_log(path, start_frame=start_frame)
        errors.extend(f"{raw_path}: {error}" for error in parsed_errors)
        log["errors"].extend(parsed_errors)
        log["event_count"] = len(parsed_events)
        log["button_event_count"] = sum(len(event["buttons"]) for event in parsed_events)
        if parsed_events:
            frame = max(int(event["end_frame"]) for event in parsed_events)
        log["total_frames"] = frame - start_frame
        events.extend(parsed_events)
        logs.append(log)
    truncated = bool(max_events and len(events) > max_events)
    if truncated:
        warnings.append(f"input playback events truncated in report at {max_events} of {len(events)}")
    button_sample = unique_list(
        button.upper()
        for event in events
        for button in event.get("buttons", [])
    )[:12]
    return {
        "schema_version": 1,
        "kind": "unified_debugger_input_playback",
        "valid": not errors,
        "input_logs": list(input_logs),
        "input_log_count": len(input_logs),
        "log_count": len(logs),
        "logs": logs,
        "event_count": len(events),
        "button_event_count": sum(len(event["buttons"]) for event in events),
        "input_frame_count": sum(1 for event in events if event.get("buttons")),
        "total_frames": frame,
        "button_sample": button_sample,
        "errors": errors,
        "warnings": warnings,
        "events": events if not max_events else events[:max_events],
        "event_report_truncated": truncated,
        "known_limits": [
            "Text input logs use one step per non-empty line: A, LEFT+START, WAIT 30, or A 8.",
            "Button names are mapped to PyBoy button names and pressed at the scheduled frame with the requested hold-frame delay.",
            "This is deterministic button playback for supported text logs; it is not a full movie format with emulator hardware timing metadata.",
        ],
    }


def parse_input_log(path: Path, *, start_frame: int = 0) -> tuple[list[dict[str, Any]], list[str]]:
    events: list[dict[str, Any]] = []
    errors: list[str] = []
    frame = start_frame
    for line_number, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        wait_match = WAIT_RE.match(line)
        if wait_match:
            wait_frames = positive_int(wait_match.group("frames"))
            if wait_frames < 1:
                errors.append(f"line {line_number}: wait frame count must be positive")
                continue
            events.append(input_event(frame=frame, raw=raw, source=path, line_number=line_number, buttons=(), hold_frames=0, advance_frames=wait_frames))
            frame += wait_frames
            continue
        buttons, hold_frames, parse_errors = parse_button_line(line)
        if parse_errors:
            errors.extend(f"line {line_number}: {error}" for error in parse_errors)
            continue
        events.append(
            input_event(
                frame=frame,
                raw=raw,
                source=path,
                line_number=line_number,
                buttons=buttons,
                hold_frames=hold_frames,
                advance_frames=max(1, hold_frames),
            )
        )
        frame += max(1, hold_frames)
    if not events and not errors:
        errors.append("input log is empty")
    return events, errors


def parse_button_line(line: str) -> tuple[tuple[str, ...], int, list[str]]:
    parts = [part for part in re.split(r"[\s,+|;]+", line.strip()) if part]
    if not parts:
        return (), 1, ["empty input line"]
    hold_frames = 1
    if parts and parts[-1].isdigit():
        hold_frames = positive_int(parts[-1])
        parts = parts[:-1]
    if hold_frames < 1:
        return (), hold_frames, ["button hold frame count must be positive"]
    buttons: list[str] = []
    errors: list[str] = []
    for part in parts:
        button = BUTTON_ALIASES.get(part.upper())
        if button is None:
            errors.append(f"unknown button {part!r}")
            continue
        buttons.append(button)
    buttons = unique_list(buttons)
    if not buttons and not errors:
        errors.append("input line has no buttons")
    return tuple(buttons), hold_frames, errors


def input_event(
    *,
    frame: int,
    raw: str,
    source: Path,
    line_number: int,
    buttons: tuple[str, ...],
    hold_frames: int,
    advance_frames: int,
) -> dict[str, Any]:
    return {
        "frame": int(frame),
        "end_frame": int(frame) + max(1, int(advance_frames)),
        "source": str(source),
        "line": int(line_number),
        "raw": raw,
        "buttons": list(buttons),
        "hold_frames": int(hold_frames),
        "advance_frames": max(1, int(advance_frames)),
    }


def play_inputs_for_frame(pyboy: Any, playback: dict[str, Any], frame: int) -> list[dict[str, Any]]:
    played: list[dict[str, Any]] = []
    if not playback.get("valid", True):
        return played
    for event in playback.get("events", []):
        if not isinstance(event, dict) or int(event.get("frame", -1)) != int(frame):
            continue
        buttons = [str(button) for button in event.get("buttons", []) if button]
        if not buttons:
            played.append({"frame": frame, "buttons": [], "line": event.get("line"), "wait": True})
            continue
        delay = max(1, int(event.get("hold_frames", 1) or 1))
        for button in buttons:
            pyboy.button(button, delay=delay)
        played.append(
            {
                "frame": frame,
                "buttons": buttons,
                "hold_frames": delay,
                "line": event.get("line"),
                "source": event.get("source", ""),
            }
        )
    return played


def resolve_path(raw_path: str, *, root: Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return root / path


def display_path(path: Path, *, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path)


def positive_int(value: Any) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return 0
    return number if number > 0 else 0


def unique_list(values: Any) -> list[Any]:
    out: list[Any] = []
    seen: set[Any] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out
