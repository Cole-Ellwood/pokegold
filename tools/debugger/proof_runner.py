from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Any

from .catalog import ROOT
from .next_steps import build_next_step
from .workflow import command_is_runnable, tail


SAFE_COMMAND_PREFIXES = (
    "python tools\\audit\\check_",
    "python tools/audit/check_",
    "python tools\\verify_sha1.py",
    "python tools/verify_sha1.py",
    "python -m tools.debugger grass-regrowth",
    "python -m tools.debugger content-mirror",
    "python -m tools.debugger wram-bank-hazards",
    "python -m tools.debugger learnset-inspect",
    "python -m tools.damage_debugger.matchup",
    "python -m tools.damage_debugger.clobber_smoke",
    "python -m tools.boss_ai_debugger coach-plan-templates",
)

DENIED_COMMAND_PARTS = (
    " --update",
    " generate ",
    " run-suite ",
    " --execute",
    " --execute-watch",
    " pgoal ",
    " git ",
)


def build_proof_card(
    *,
    symptom: str,
    changed_files: tuple[str, ...] = (),
    execute: bool = False,
    timeout_seconds: int = 120,
    prefer: str = "first",
    root: Path = ROOT,
) -> dict[str, Any]:
    next_step = build_next_step(symptom=symptom, changed_files=changed_files, root=root)
    rec = next_step["recommendation"]
    candidates = proof_commands(rec, prefer=prefer)
    command_records = [command_record(command) for command in candidates]
    chosen = next((item for item in command_records if item["runnable"] and item["safe"]), None)
    execution: dict[str, Any] | None = None
    if execute and chosen is not None:
        execution = execute_command(
            chosen["command"],
            root=root,
            timeout_seconds=timeout_seconds,
        )

    proof_depth = "planned"
    if chosen is not None:
        proof_depth = "executed" if execution is not None else "runnable"

    return {
        "schema_version": 1,
        "kind": "unified_debugger_proof_card",
        "root": str(root),
        "symptom": symptom,
        "changed_files": list(changed_files),
        "matched_lane": next_step["matched_lane"],
        "symptom_class": rec["symptom_class"],
        "title": rec["title"],
        "proof_depth": proof_depth,
        "valid": True,
        "passed": execution is None or execution["status"] == "passed",
        "executed": execution is not None,
        "chosen_command": chosen["command"] if chosen is not None else "",
        "command_candidates": command_records,
        "execution": execution,
        "source_refs": list(rec.get("source_refs", [])),
        "evidence_standard": list(rec.get("evidence_standard", [])),
        "disproof_standard": list(rec.get("disproof_standard", [])),
        "proof_limit": rec["proof_limit"],
        "regression_gate": rec["regression_gate"],
        "required_inputs": list(rec.get("required_inputs", [])),
        "next_step": next_step,
    }


def proof_commands(rec: dict[str, Any], *, prefer: str) -> list[str]:
    ordered = {
        "first": [
            rec.get("first_command", ""),
            rec.get("regression_gate", ""),
            rec.get("escalation_command", ""),
        ],
        "gate": [
            rec.get("regression_gate", ""),
            rec.get("first_command", ""),
            rec.get("escalation_command", ""),
        ],
        "escalation": [
            rec.get("escalation_command", ""),
            rec.get("regression_gate", ""),
            rec.get("first_command", ""),
        ],
    }[prefer]
    out: list[str] = []
    for command in ordered:
        if command and command not in out:
            out.append(str(command))
    return out


def command_record(command: str) -> dict[str, Any]:
    return {
        "command": command,
        "runnable": command_is_runnable(command),
        "safe": command_is_safe(command),
    }


def command_is_safe(command: str) -> bool:
    normalized = " ".join(command.strip().split())
    if not command_is_runnable(normalized):
        return False
    if any(part in normalized for part in DENIED_COMMAND_PARTS):
        return False
    return normalized.startswith(SAFE_COMMAND_PREFIXES)


def execute_command(command: str, *, root: Path, timeout_seconds: int) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "failed",
            "returncode": None,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "stdout_tail": tail(exc.stdout or ""),
            "stderr_tail": tail((exc.stderr or "") + "\ncommand timed out"),
        }

    return {
        "status": "passed" if completed.returncode == 0 else "failed",
        "returncode": completed.returncode,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "stdout_tail": tail(completed.stdout),
        "stderr_tail": tail(completed.stderr),
    }
