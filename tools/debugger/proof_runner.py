from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Any

from .catalog import ROOT
from .next_steps import NEXT_STEP_ROWS, build_next_step
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
    "python -m tools.boss_ai_debugger rom-switch-materialize",
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

DENIED_SHELL_CHARS = ("&", "|", ";", "\n", "\r")


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
    blocked_reason = blocked_reason_for_command(command)
    return {
        "command": command,
        "runnable": command_is_runnable(command),
        "safe": blocked_reason is None,
        "blocked_reason": blocked_reason,
    }


def command_is_safe(command: str) -> bool:
    return blocked_reason_for_command(command) is None


def blocked_reason_for_command(command: str) -> str | None:
    normalized = " ".join(command.strip().split())
    if not normalized:
        return "empty_command"
    if not command_is_runnable(normalized):
        return "placeholder_input"
    for char in DENIED_SHELL_CHARS:
        if char in normalized:
            return "shell_metacharacter"
    for part in DENIED_COMMAND_PARTS:
        if part in normalized:
            return f"denied:{part.strip()}"
    if not normalized.startswith(SAFE_COMMAND_PREFIXES):
        return "unsafe_prefix"
    return None


def execute_command(command: str, *, root: Path, timeout_seconds: int) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command.split(),
            cwd=root,
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


def build_proof_campaign(
    *,
    cases: tuple[dict[str, Any], ...],
    execute: bool = False,
    timeout_seconds: int = 120,
    max_commands: int = 50,
    include_all_routes: bool = False,
    root: Path = ROOT,
) -> dict[str, Any]:
    started = time.perf_counter()
    records: dict[str, dict[str, Any]] = {}
    route_row_count = 0
    route_symptom_classes: set[str] = set()

    if include_all_routes:
        route_row_count = len(NEXT_STEP_ROWS)
        for row in NEXT_STEP_ROWS:
            symptom_class = str(row.get("symptom_class", ""))
            route_symptom_classes.add(symptom_class)
            for command in proof_commands(row, prefer="first"):
                add_campaign_command(
                    records,
                    command=command,
                    source_id=f"route:{symptom_class}",
                    symptom_class=symptom_class,
                    expected_exit_codes=(0,),
                    expected_stdout_contains=(),
                    expected_disposition="passed",
                    execute_requested=False,
                )

    case_results: list[dict[str, Any]] = []
    for index, case in enumerate(cases, 1):
        case_id = str(case.get("id") or f"case_{index:02d}")
        commands = case_commands(case, root=root)
        expected_exit_codes = tuple(int(item) for item in case.get("expected_exit_codes", [0]))
        expected_stdout_contains = tuple(str(item) for item in case.get("expected_stdout_contains", []))
        expected_disposition = str(case.get("expected_disposition") or "passed")
        symptom_class = str(case.get("expected_class") or case.get("symptom_class") or "")
        case_command_keys: list[str] = []
        for command in commands:
            record = add_campaign_command(
                records,
                command=command,
                source_id=f"case:{case_id}",
                symptom_class=symptom_class,
                expected_exit_codes=expected_exit_codes,
                expected_stdout_contains=expected_stdout_contains,
                expected_disposition=expected_disposition,
                execute_requested=True,
            )
            case_command_keys.append(record["key"])
        case_results.append(
            {
                "id": case_id,
                "expected_disposition": expected_disposition,
                "command_keys": case_command_keys,
            }
        )

    executable = [
        record
        for record in records.values()
        if record["execute_requested"] and record["safe"] and record["runnable"]
    ]
    executed_count = 0
    unsafe_execution_attempts = 0
    if execute:
        for record in executable:
            if executed_count >= max_commands:
                record["disposition"] = "not_run_limit"
                continue
            if not record["safe"]:
                unsafe_execution_attempts += 1
                continue
            execution = execute_command(record["command"], root=root, timeout_seconds=timeout_seconds)
            record["execution"] = execution
            record["executed"] = True
            record["disposition"] = disposition_for_execution(
                execution,
                expected_exit_codes=tuple(record["expected_exit_codes"]),
                expected_stdout_contains=tuple(record["expected_stdout_contains"]),
            )
            executed_count += 1

    for record in records.values():
        if record["executed"]:
            continue
        if record["blocked_reason"]:
            record["disposition"] = "blocked_placeholder" if record["blocked_reason"] == "placeholder_input" else "unsafe_rejected"
        elif record["execute_requested"] and not execute:
            record["disposition"] = "planned"
        elif not record["execute_requested"]:
            record["disposition"] = "classified"

    command_records = sorted(records.values(), key=lambda item: item["key"])
    status_counts = count_by(command_records, "disposition")
    blocked_reason_counts = count_by(
        [record for record in command_records if record.get("blocked_reason")],
        "blocked_reason",
    )
    failed_count = status_counts.get("failed", 0)
    valid = failed_count == 0 and unsafe_execution_attempts == 0

    return {
        "schema_version": 1,
        "kind": "unified_debugger_proof_campaign",
        "root": str(root),
        "valid": valid,
        "execute": execute,
        "include_all_routes": include_all_routes,
        "route_row_count": route_row_count,
        "classified_symptom_class_count": len(route_symptom_classes),
        "case_count": len(cases),
        "unique_command_count": len(command_records),
        "executed_unique_command_count": sum(1 for record in command_records if record["executed"]),
        "unsafe_execution_attempts": unsafe_execution_attempts,
        "status_counts": status_counts,
        "blocked_reason_counts": blocked_reason_counts,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "case_results": case_results,
        "command_records": command_records,
    }


def case_commands(case: dict[str, Any], *, root: Path) -> list[str]:
    if "command" in case:
        return [str(case["command"])]
    if "commands" in case:
        return [str(command) for command in case["commands"]]
    symptom = str(case.get("symptom", ""))
    if symptom:
        next_step = build_next_step(
            symptom=symptom,
            changed_files=tuple(str(item) for item in case.get("changed_files", [])),
            root=root,
        )
        return proof_commands(next_step["recommendation"], prefer=str(case.get("prefer", "first")))
    return []


def add_campaign_command(
    records: dict[str, dict[str, Any]],
    *,
    command: str,
    source_id: str,
    symptom_class: str,
    expected_exit_codes: tuple[int, ...],
    expected_stdout_contains: tuple[str, ...],
    expected_disposition: str,
    execute_requested: bool,
) -> dict[str, Any]:
    key = " ".join(command.strip().split())
    if key not in records:
        base = command_record(command)
        records[key] = {
            "key": key,
            "command": command,
            "runnable": base["runnable"],
            "safe": base["safe"],
            "blocked_reason": base["blocked_reason"],
            "sources": [],
            "symptom_classes": [],
            "expected_exit_codes": list(expected_exit_codes),
            "expected_stdout_contains": list(expected_stdout_contains),
            "expected_disposition": expected_disposition,
            "execute_requested": execute_requested,
            "executed": False,
            "execution": None,
            "disposition": "pending",
        }
    record = records[key]
    if source_id not in record["sources"]:
        record["sources"].append(source_id)
    if symptom_class and symptom_class not in record["symptom_classes"]:
        record["symptom_classes"].append(symptom_class)
    if execute_requested:
        record["execute_requested"] = True
        record["expected_exit_codes"] = list(expected_exit_codes)
        record["expected_stdout_contains"] = list(expected_stdout_contains)
        record["expected_disposition"] = expected_disposition
    return record


def disposition_for_execution(
    execution: dict[str, Any],
    *,
    expected_exit_codes: tuple[int, ...],
    expected_stdout_contains: tuple[str, ...],
) -> str:
    returncode = execution.get("returncode")
    stdout = "\n".join(execution.get("stdout_tail", []))
    stderr = "\n".join(execution.get("stderr_tail", []))
    combined = stdout + "\n" + stderr
    if returncode not in expected_exit_codes:
        return "failed"
    if any(expected not in combined for expected in expected_stdout_contains):
        return "failed"
    return "passed" if returncode == 0 else "discrepancy_found"


def count_by(records: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        key = str(record.get(field) or "")
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))
