from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Any

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
    return "<" not in command and ">" not in command


def execute_step(step: dict[str, Any], *, root: Path, timeout_seconds: int) -> None:
    if not step["runnable"]:
        step["status"] = "skipped"
        step["stderr_tail"] = ["command contains a placeholder and needs a concrete artifact"]
        return
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            step["command"],
            cwd=root,
            shell=True,
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
    step["elapsed_seconds"] = time.perf_counter() - started
    step["returncode"] = completed.returncode
    step["stdout_tail"] = tail(completed.stdout)
    step["stderr_tail"] = tail(completed.stderr)
    step["status"] = "passed" if completed.returncode == 0 else "failed"


def tail(text: str, *, max_lines: int = 12) -> list[str]:
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    return lines[-max_lines:]
