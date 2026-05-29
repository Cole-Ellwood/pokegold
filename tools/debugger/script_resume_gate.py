from __future__ import annotations

from pathlib import Path
from typing import Any

from .catalog import ROOT
from .reporting import load_reports
from .workflow import command_is_runnable


REQUIRED_TRAINER_RESUME_WATCHES = (
    "wSeenTrainerBank",
    "wScriptAfterPointer",
    "wRunningTrainerBattleScript",
    "wScriptBank",
    "wScriptPos",
)
SCRIPT_RESUME_ACTIVITY_WATCHES = {
    "wScriptAfterPointer",
    "wRunningTrainerBattleScript",
    "wScriptBank",
    "wScriptPos",
    "wScriptRunning",
    "wScriptMode",
}


def build_script_resume_gate_report(
    *,
    reports: tuple[str, ...],
    root: Path = ROOT,
) -> dict[str, Any]:
    loaded, load_errors = load_reports(reports=reports, root=root)
    findings: list[dict[str, Any]] = []
    warnings: list[str] = []
    for loaded_report in loaded:
        source = str(loaded_report.get("source", "report"))
        data = loaded_report.get("data", {})
        if not isinstance(data, dict):
            continue
        kind = str(data.get("kind", ""))
        if kind == "unified_debugger_runtime_state_report":
            findings.extend(findings_from_runtime_state(data, source=source))
        elif kind == "unified_debugger_save_state_inspection":
            findings.extend(findings_from_state_inspection(data, source=source))
        elif kind == "unified_debugger_watch_report":
            findings.extend(findings_from_watch_report(data, source=source))
        else:
            warnings.append(f"{source}: unsupported report kind for script-resume gate: {kind or '<missing>'}")
    if not loaded and not load_errors:
        load_errors.append("at least one --report is required")
    failed = [finding for finding in findings if finding["severity"] == "error"]
    commands = [
        "python -m tools.debugger state-inspect --save-state <state.sgm> --symbols pokegold.sym --rom pokegold.gbc --json-out .local\\tmp\\state_inspect.json",
        "python -m tools.debugger watch --reset-sentinel --watch-symbol wSeenTrainerBank --watch-symbol wScriptAfterPointer --watch-symbol wRunningTrainerBattleScript --watch-symbol wScriptBank --watch-symbol wScriptPos --save-state <before-trigger.state> --execute --json-out .local\\tmp\\script_resume_watch.json",
        "python -m tools.debugger watch --reset-sentinel --watch-symbol wSeenTrainerBank --watch-symbol wScriptAfterPointer --watch-symbol wRunningTrainerBattleScript --watch-symbol wScriptBank --watch-symbol wScriptPos --battery-save pokegold.sav --out-initial-state .local\\tmp\\script_resume_continue.state --input <frame:button[:delay]> --execute --json-out .local\\tmp\\script_resume_watch.json",
        "python -m tools.debugger wram-lifetime --symbol wSeenTrainerBank --symbol wScriptAfterPointer --symbol wRunningTrainerBattleScript --through Script_startbattle",
    ]
    return {
        "schema_version": 1,
        "kind": "unified_debugger_script_resume_gate",
        "root": str(root),
        "valid": not load_errors,
        "passed": not load_errors and not failed and bool(loaded),
        "input_reports": [item["source"] for item in loaded],
        "finding_count": len(findings),
        "findings": findings,
        "error_count": len(load_errors),
        "warning_count": len(warnings),
        "errors": load_errors,
        "warnings": warnings,
        "commands": commands,
        "runnable_commands": [command for command in commands if command_is_runnable(command)],
        "blocked_commands": [command for command in commands if not command_is_runnable(command)],
        "known_limits": [
            "This gate proves absence of known script-resume crash signals in supplied reports; it does not synthesize the trainer/evolution state by itself.",
            "For forward replay, use a state before the battle/evolution trigger, not an already-corrupted crash state.",
        ],
    }


def findings_from_state_inspection(data: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    diagnostics = data.get("diagnostics", {}) if isinstance(data.get("diagnostics"), dict) else {}
    raw_findings = data.get("findings", diagnostics.get("findings", []))
    for finding in raw_findings:
        if not isinstance(finding, dict):
            continue
        copied = dict(finding)
        copied["source"] = source
        severity = copied.get("severity")
        if isinstance(severity, int):
            copied["severity"] = "error" if severity <= 2 else "info"
        if "summary" not in copied and "title" in copied:
            copied["summary"] = copied["title"]
        out.append(copied)
    if not out and (diagnostics.get("status") == "ok" or data.get("blocking_finding_count") == 0):
        out.append(
            {
                "id": "state_inspection_ok",
                "severity": "info",
                "source": source,
                "summary": "state inspection did not find impossible script state",
                "evidence": [],
            }
        )
    return out


def findings_from_runtime_state(data: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for finding in data.get("findings", []):
        if not isinstance(finding, dict):
            continue
        severity = int(finding.get("severity", 0) or 0)
        out.append(
            {
                "id": str(finding.get("id", "runtime_state_finding")),
                "severity": "error" if severity >= 85 else "warning",
                "source": source,
                "summary": str(finding.get("title", "")),
                "evidence": [str(item) for item in finding.get("evidence", [])],
            }
        )
    if not out:
        out.append(
            {
                "id": "runtime_state_ok",
                "severity": "info",
                "source": source,
                "summary": "runtime state report did not find impossible script or CPU state",
                "evidence": [],
            }
        )
    return out


def findings_from_watch_report(data: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not data.get("valid", False):
        out.append(
            {
                "id": "watch_report_invalid",
                "severity": "error",
                "source": source,
                "summary": "watch report is invalid",
                "evidence": [str(error) for error in data.get("errors", [])],
            }
        )
    if not data.get("executed", False):
        out.append(
            {
                "id": "watch_not_executed",
                "severity": "error",
                "source": source,
                "summary": "watch report was planned but not executed",
                "evidence": ["run watch with --execute before treating this gate as proof"],
            }
        )
    if int(data.get("frames", 0) or 0) < 1:
        out.append(
            {
                "id": "watch_too_short",
                "severity": "error",
                "source": source,
                "summary": "watch report did not advance the emulator",
                "evidence": ["frames must be at least 1 for script-resume gate proof"],
            }
        )
    watch_names = {
        str(watch.get("name"))
        for watch in data.get("watches", [])
        if isinstance(watch, dict) and watch.get("found")
    }
    missing_watches = [
        symbol for symbol in REQUIRED_TRAINER_RESUME_WATCHES if symbol not in watch_names
    ]
    if missing_watches:
        out.append(
            {
                "id": "required_watch_symbol_missing",
                "severity": "error",
                "source": source,
                "summary": "trainer resume watch report is missing required symbols",
                "evidence": [f"missing={','.join(missing_watches)}"],
            }
        )
    if not data.get("reset_sentinel", False):
        out.append(
            {
                "id": "reset_sentinel_not_enabled",
                "severity": "error",
                "source": source,
                "summary": "watch report did not enable reset/start sentinels",
                "evidence": ["run watch with --reset-sentinel"],
            }
        )
    if int(data.get("hit_count", 0) or 0) < 1:
        out.append(
            {
                "id": "watch_no_runtime_signal",
                "severity": "error",
                "source": source,
                "summary": "watch report did not observe any watched runtime change",
                "evidence": ["a clean pass needs at least one watched trainer/script signal to prove the route executed"],
            }
        )
    elif not has_script_resume_activity(data):
        out.append(
            {
                "id": "watch_no_script_resume_signal",
                "severity": "error",
                "source": source,
                "summary": "watch report did not observe script/resume activity",
                "evidence": [
                    "trainer-bank-only or unrelated union churn is not enough for post-battle resume proof"
                ],
            }
        )
    runtime_summary = data.get("runtime_summary", {})
    if not has_pc_sp_snapshot(runtime_summary, "initial") or not has_pc_sp_snapshot(runtime_summary, "final"):
        out.append(
            {
                "id": "pc_sp_snapshot_missing",
                "severity": "error",
                "source": source,
                "summary": "watch report does not include initial and final PC/SP snapshots",
                "evidence": ["runtime_summary.initial/final registers must include register_pc and register_sp"],
            }
        )
    reset_count = int(data.get("reset_event_count", 0) or 0)
    if reset_count:
        out.append(
            {
                "id": "reset_sentinel",
                "severity": "error",
                "source": source,
                "summary": "reset/start sentinel was hit during replay",
                "evidence": [f"reset_event_count={reset_count}"],
            }
        )
    for event in data.get("events", []):
        if not isinstance(event, dict) or event.get("event_type") != "invalid_script_state":
            continue
        out.append(
            {
                "id": "invalid_script_state",
                "severity": "error",
                "source": source,
                "summary": "watch replay observed an impossible script state",
                "evidence": [
                    str(event.get("script", "")),
                    *[str(reason) for reason in event.get("reasons", [])],
                ],
            }
        )
    if not out:
        out.append(
            {
                "id": "watch_script_resume_ok",
                "severity": "info",
                "source": source,
                "summary": "watch report had no reset sentinel or impossible script-state event",
                "evidence": [],
            }
        )
    return out


def has_pc_sp_snapshot(runtime_summary: Any, key: str) -> bool:
    if not isinstance(runtime_summary, dict):
        return False
    snapshot = runtime_summary.get(key)
    if not isinstance(snapshot, dict):
        return False
    registers = snapshot.get("registers")
    return isinstance(registers, dict) and bool(registers.get("register_pc")) and bool(registers.get("register_sp"))


def has_script_resume_activity(data: dict[str, Any]) -> bool:
    for event in data.get("events", []):
        if not isinstance(event, dict):
            continue
        if event.get("event_type") == "invalid_script_state":
            return True
        if str(event.get("watch", "")) in SCRIPT_RESUME_ACTIVITY_WATCHES:
            return True
    return False
