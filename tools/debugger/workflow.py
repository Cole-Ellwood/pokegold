from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Any

from .address import command_address_text
from .catalog import ROOT, triage_request


MATCH_PRIORITIES = {
    "damage_chain": 10,
    "boss_ai": 10,
    "banking_and_abi": 20,
    "graphics_audio_maps": 30,
    "general": 40,
}


def build_gate_plan(
    *,
    changed_files: tuple[str, ...] = (),
    symptom: str = "",
    execute: bool = False,
    max_commands: int | None = None,
    timeout_seconds: int = 600,
    root: Path = ROOT,
) -> dict[str, Any]:
    triage = triage_request(
        changed_files=changed_files,
        symptom=symptom,
        root=root,
    )
    steps = gate_steps_from_triage(triage)
    if max_commands is not None:
        steps = steps[:max_commands]
    if execute:
        for step in steps:
            execute_step(step, root=root, timeout_seconds=timeout_seconds)
    else:
        for step in steps:
            step["status"] = "planned"

    failed = [step for step in steps if step["status"] == "failed"]
    skipped = [step for step in steps if step["status"] == "skipped"]
    return {
        "schema_version": 1,
        "kind": "unified_debugger_gate_plan",
        "root": str(root),
        "changed_files": list(changed_files),
        "symptom": symptom,
        "executed": execute,
        "passed": execute and not failed,
        "step_count": len(steps),
        "failed_count": len(failed),
        "skipped_count": len(skipped),
        "triage_matches": triage["matches"],
        "steps": steps,
    }


def gate_steps_from_triage(triage: dict[str, Any]) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    seen_commands: set[str] = set()
    for match in triage["matches"]:
        priority = MATCH_PRIORITIES.get(match["id"], 50)
        for command in match["commands"]:
            if command in seen_commands:
                continue
            seen_commands.add(command)
            steps.append(
                {
                    "id": f"{match['id']}:{len(steps) + 1}",
                    "match_id": match["id"],
                    "title": match["title"],
                    "priority": priority,
                    "command": command,
                    "runnable": command_is_runnable(command),
                    "status": "pending",
                    "returncode": None,
                    "elapsed_seconds": 0.0,
                    "stdout_tail": [],
                    "stderr_tail": [],
                }
            )
    return sorted(steps, key=lambda step: (step["priority"], step["id"]))


def command_is_runnable(command: str) -> bool:
    text = str(command)
    if "<" in text or ">" in text:
        return False
    return not any(command_part_is_placeholder(part) for part in command_parts(text))


def command_part_is_placeholder(part: str) -> bool:
    normalized = strip_command_quotes(part).strip().replace("/", "\\").lower()
    return normalized.startswith("path\\to\\")


def command_address_arg(address: Any) -> str:
    return command_address_text(address)


def command_parts(command: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    quote = ""
    for char in str(command):
        if quote:
            if char == quote:
                quote = ""
            else:
                current.append(char)
            continue
        if char in {"\"", "'"}:
            quote = char
            continue
        if char.isspace():
            if current:
                parts.append("".join(current))
                current = []
            continue
        current.append(char)
    if current:
        parts.append("".join(current))
    return parts


def command_option_values(command: str, option: str) -> list[str]:
    values: list[str] = []
    parts = command_parts(command)
    for index, part in enumerate(parts):
        if part == option and index + 1 < len(parts):
            values.append(parts[index + 1])
        elif part.startswith(option + "="):
            values.append(strip_command_quotes(part.split("=", 1)[1]))
    return unique_texts(values)


def strip_command_quotes(value: str) -> str:
    text = str(value)
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"\"", "'"}:
        return text[1:-1]
    return text


def unique_texts(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value)
        if text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def execute_step(step: dict[str, Any], *, root: Path, timeout_seconds: int) -> None:
    if not step["runnable"]:
        step["status"] = "skipped"
        step["stderr_tail"] = ["command contains a placeholder and needs a concrete artifact"]
        return
    argv = command_parts(str(step.get("command", "")))
    if not argv:
        step["status"] = "skipped"
        step["stderr_tail"] = ["empty command"]
        return
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            argv,
            cwd=root,
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        step["status"] = "failed"
        step["returncode"] = None
        step["elapsed_seconds"] = time.perf_counter() - started
        step["stdout_tail"] = tail(exc.stdout or "")
        step["stderr_tail"] = tail((exc.stderr or "") + "\ncommand timed out")
        return
    except OSError as exc:
        step["status"] = "failed"
        step["returncode"] = None
        step["elapsed_seconds"] = time.perf_counter() - started
        step["stdout_tail"] = []
        step["stderr_tail"] = tail(str(exc))
        return
    step["elapsed_seconds"] = time.perf_counter() - started
    step["returncode"] = completed.returncode
    step["stdout_tail"] = tail(completed.stdout)
    step["stderr_tail"] = tail(completed.stderr)
    step["status"] = "passed" if completed.returncode == 0 else "failed"


def tail(text: str, *, max_lines: int = 12) -> list[str]:
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    return lines[-max_lines:]
