from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .catalog import ROOT


SEVERITY_BASE = {
    "gate_failed": 95,
    "ingest_error": 85,
    "workflow_failed": 82,
    "watch_hit": 75,
    "capability_missing": 78,
    "capability_partial": 64,
    "compare_gap": 55,
    "fuzz_campaign": 62,
    "content_mirror_failed": 76,
    "content_mirror_warning": 35,
    "content_scenario": 46,
    "content_state_blocked": 68,
    "content_state_executed": 62,
    "content_state_ready": 58,
    "state_space_blocked": 68,
    "state_space_executed": 62,
    "state_space_ready": 58,
    "setup_trigger_gap": 64,
    "runtime_state_impossible": 88,
    "save_state_anomaly": 88,
    "expectation_failed": 78,
    "mirror_uncovered": 50,
    "test_gap": 45,
    "coverage_gap": 40,
    "taint_path": 66,
    "reverse_attribution": 70,
    "instruction_trace_miss": 74,
    "instruction_trace_partial": 64,
    "instruction_trace_limit": 68,
    "instruction_trace_ready": 60,
    "next_step": 52,
    "provenance_warning": 30,
    "ingest_warning": 25,
}

ROM_SURFACE_SEVERITY_HINTS = (
    (
        "banking_abi",
        "ROM banking / ABI",
        10,
        (
            "home/",
            "macros/",
            "farcall",
            "bankswitch",
            "hrombank",
            "hloadedrombank",
            "rst ",
            "rstvector",
            "banked",
        ),
    ),
    (
        "battle_damage",
        "Battle damage",
        8,
        (
            "wcurdamage",
            "battlecommand_damage",
            "engine/battle/effect_commands",
            "damage",
            "type chart",
            "type matchup",
            "held item",
            "weather",
        ),
    ),
    (
        "boss_ai",
        "Boss AI",
        8,
        (
            "bossai_",
            "wbossai",
            "wenemyaimovescores",
            "engine/battle/ai/",
            "boss ai",
            "policy",
            "selector",
        ),
    ),
    (
        "event_scripts_maps",
        "Event scripts and maps",
        7,
        (
            "engine/events/",
            "engine/overworld/",
            "maps/",
            "scripts/",
            "runscriptcommand",
            "callscript",
            "wscriptpos",
            "warp_event",
            "bg_event",
            "object_event",
            "mapscripts",
        ),
    ),
    (
        "movement_text",
        "Movement and text",
        6,
        (
            "data/moves/movement",
            "movement",
            "applymovement",
            "handlemovementdata",
            "wmovementpointer",
            "text/",
            "charmap",
        ),
    ),
    (
        "graphics_audio_ui",
        "Graphics, audio, and UI",
        5,
        (
            "gfx/",
            "audio/",
            "tilesets/",
            "palette",
            "tilemap",
            "sprite",
            "song",
            "sfx",
            "menu",
            "window",
        ),
    ),
    (
        "pokemon_move_data",
        "Pokemon and move data",
        4,
        (
            "data/pokemon/",
            "data/moves/",
            "base_stats",
            "learnsets",
            "evolutions",
            "tmhm",
        ),
    ),
)


def rank_findings(
    *,
    reports: tuple[str, ...],
    root: Path = ROOT,
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    errors: list[str] = []
    for report_path in reports:
        path = resolve_path(report_path, root=root)
        if not path.exists():
            errors.append(f"missing report: {report_path}")
            continue
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{report_path}: invalid JSON: {exc.msg}")
            continue
        findings.extend(findings_from_report(report, source=display_path(path, root=root)))

    findings = [calibrate_finding_severity(finding) for finding in findings]
    findings.sort(
        key=lambda item: (
            -int(item["severity"]),
            -float(item["confidence"]),
            item["source"],
            item["title"],
        )
    )
    return {
        "schema_version": 1,
        "kind": "unified_debugger_ranked_findings",
        "root": str(root),
        "valid": not errors,
        "report_count": len(reports),
        "error_count": len(errors),
        "errors": errors,
        "finding_count": len(findings),
        "findings": findings,
    }


def findings_from_report(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    kind = report.get("kind", "")
    builder = _FINDINGS_BUILDERS.get(kind)
    if builder is not None:
        return builder(report, source=source)
    return [
        finding(
            finding_type="unknown_report",
            title=f"Unsupported report kind: {kind or '<missing>'}",
            source=source,
            severity=20,
            confidence=0.2,
            evidence=[source],
            next_actions=["python -m tools.debugger ingest --changed-file <report-producer>"],
        )
    ]


def ingest_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for artifact in report.get("artifacts", []):
        for error in artifact.get("errors", []):
            out.append(
                finding(
                    finding_type="ingest_error",
                    title=f"Ingest error in {artifact.get('kind')}: {artifact.get('path')}",
                    source=source,
                    severity=SEVERITY_BASE["ingest_error"],
                    confidence=0.95,
                    evidence=[error],
                    next_actions=["Fix or regenerate the artifact before replay/localization."],
                )
            )
        for warning in artifact.get("warnings", []):
            out.append(
                finding(
                    finding_type="ingest_warning",
                    title=f"Ingest warning in {artifact.get('kind')}: {artifact.get('path')}",
                    source=source,
                    severity=SEVERITY_BASE["ingest_warning"],
                    confidence=0.7,
                    evidence=[warning],
                    next_actions=["Inspect artifact metadata before trusting downstream output."],
                )
            )
    return out


def capability_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    ready = bool(report.get("ready"))
    status_counts = report.get("status_counts") if isinstance(report.get("status_counts"), dict) else {}
    shared_evidence = [
        f"ready={ready}",
        "status_counts="
        + ",".join(f"{name}={count}" for name, count in sorted(status_counts.items())),
        f"blocking_gap_count={report.get('blocking_gap_count', 0)}",
    ]
    for capability in dict_items(report.get("capabilities")):
        status = str(capability.get("status") or "")
        if status == "complete":
            continue
        finding_type = "capability_missing" if status == "missing" else "capability_partial"
        title = str(capability.get("title") or capability.get("id") or "<unknown>")
        gaps = string_items(capability.get("gaps"))
        gap_actions = dict_items(capability.get("gap_actions"))
        action_evidence: list[str] = []
        action_commands: list[str] = []
        for action in gap_actions[:3]:
            action_evidence.append(
                "gap_action="
                f"{action.get('id', '<unknown>')}"
                f"; scenario={action.get('lived_scenario', '<unspecified>')}"
            )
            action_evidence.extend(string_items(action.get("evidence_standard"))[:2])
            action_evidence.extend(string_items(action.get("disproof_standard"))[:2])
            action_commands.extend(string_items(action.get("commands"))[:3])
            action_commands.extend(string_items(action.get("regression_gate"))[:1])
        out.append(
            finding(
                finding_type=finding_type,
                title=f"Capability {status}: {title}",
                source=source,
                severity=SEVERITY_BASE[finding_type],
                confidence=0.88 if status == "missing" else 0.78,
                evidence=[
                    *shared_evidence,
                    f"id={capability.get('id', '')}",
                    f"scope={capability.get('scope', '')}",
                    *gaps[:4],
                    *action_evidence[:8],
                ],
                next_actions=unique_string_items(action_commands)[:6]
                or string_items(capability.get("commands"))[:6]
                or ["python -m tools.debugger audit"],
            )
        )
    if not ready and not out:
        out.append(
            finding(
                finding_type="capability_partial",
                title="Debugger capability audit is not ready",
                source=source,
                severity=SEVERITY_BASE["capability_partial"],
                confidence=0.7,
                evidence=shared_evidence + string_items(report.get("blocking_gaps"))[:4],
                next_actions=["python -m tools.debugger audit"],
            )
        )
    return out


def watch_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for event in report.get("events", []):
        out.append(
            finding(
                finding_type="watch_hit",
                title=f"{event.get('watch')} changed at {event.get('pc_bank_address')}",
                source=source,
                severity=SEVERITY_BASE["watch_hit"],
                confidence=0.8,
                evidence=[
                    f"{event.get('old_hex')} -> {event.get('new_hex')}",
                    str(event.get("pc_label", "")),
                    f"context_frames={event.get('dynamic_context', {}).get('context_frame_count', 0)}",
                ],
                next_actions=string_items(event.get("commands"))[:4]
                or string_items(event.get("suggested_commands"))[:4],
            )
        )
    for error in report.get("errors", []):
        out.append(
            finding(
                finding_type="ingest_error",
                title="Watch replay setup error",
                source=source,
                severity=SEVERITY_BASE["ingest_error"],
                confidence=0.95,
                evidence=[error],
                next_actions=["Fix watch inputs and rerun `python -m tools.debugger watch`."],
            )
        )
    return out


def runtime_state_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in dict_items(report.get("findings")):
        out.append(
            finding(
                finding_type=str(item.get("type", "runtime_state_impossible")),
                title=str(item.get("title", "Runtime state invariant failed")),
                source=source,
                severity=int(item.get("severity", SEVERITY_BASE["runtime_state_impossible"])),
                confidence=float(item.get("confidence", 0.88)),
                evidence=string_items(item.get("evidence"))[:6],
                next_actions=string_items(item.get("next_actions"))[:5]
                or string_items(report.get("commands"))[:5],
            )
        )
    if report.get("passed") is False and not out:
        out.append(
            finding(
                finding_type="runtime_state_impossible",
                title="Runtime state report did not pass",
                source=source,
                severity=SEVERITY_BASE["runtime_state_impossible"],
                confidence=0.75,
                evidence=[f"state={report.get('save_state', '')}"],
                next_actions=string_items(report.get("commands"))[:5],
            )
        )
    return out


def save_state_inspection_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in dict_items(report.get("findings")):
        severity_level = int(item.get("severity", 3) or 3)
        out.append(
            finding(
                finding_type="save_state_anomaly",
                title=str(item.get("title") or item.get("id") or "Save-state anomaly"),
                source=source,
                severity={1: 94, 2: 86}.get(severity_level, 35),
                confidence=0.92 if severity_level <= 2 else 0.68,
                evidence=string_items(item.get("detail"))[:2]
                or string_items(item.get("evidence"))[:4],
                next_actions=string_items(report.get("commands"))[:5],
            )
        )
    return out


def replay_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    watch_report = report.get("watch_report")
    if isinstance(watch_report, dict):
        out.extend(watch_findings(watch_report, source=source))
    for error in report.get("errors", []):
        out.append(
            finding(
                finding_type="ingest_error",
                title="Replay setup error",
                source=source,
                severity=SEVERITY_BASE["ingest_error"],
                confidence=0.9,
                evidence=[error],
                next_actions=["Fix replay inputs and rerun `python -m tools.debugger replay`."],
            )
        )
    if not report.get("watch_symbol_count"):
        out.append(
            finding(
                finding_type="test_gap",
                title="Replay plan has no watchable symbol target",
                source=source,
                severity=SEVERITY_BASE["test_gap"],
                confidence=0.65,
                evidence=["Provide --watch-symbol, --symbol, a watch report, or a symptom with a watchable RAM target."],
                next_actions=["python -m tools.debugger replay --watch-symbol <wram_symbol>"],
            )
        )
    return out


def setup_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    target_by_surface = {
        str(target.get("surface", "")): target
        for target in report.get("targets", [])
        if isinstance(target, dict)
    }
    coverage = report.get("trigger_coverage")
    coverage_targets = coverage.get("targets", []) if isinstance(coverage, dict) else []
    for row in coverage_targets:
        if not isinstance(row, dict) or row.get("status") == "covered":
            continue
        surface = str(row.get("surface", ""))
        target = target_by_surface.get(surface, {})
        status = str(row.get("status", "planned"))
        blockers = string_items(row.get("blockers"))
        severity = SEVERITY_BASE["setup_trigger_gap"] if status == "blocked" else 52
        out.append(
            finding(
                finding_type="setup_trigger_gap",
                title=f"Setup trigger {status}: {surface or '<unknown-surface>'}",
                source=source,
                severity=severity,
                confidence=0.78 if status == "blocked" else 0.68,
                evidence=[
                    f"state={row.get('state_status', '')}",
                    f"trigger={group_status(row.get('trigger_status'))}",
                    f"validation={group_status(row.get('validation_status'))}",
                    *blockers,
                ],
                next_actions=string_items(target.get("commands"))[:6]
                or string_items(report.get("commands"))[:6],
            )
        )
    for error in report.get("errors", []):
        out.append(
            finding(
                finding_type="ingest_error",
                title="Setup planning input error",
                source=source,
                severity=SEVERITY_BASE["ingest_error"],
                confidence=0.92,
                evidence=[error],
                next_actions=["Fix setup inputs and rerun `python -m tools.debugger setup`."],
            )
        )
    return out


def gate_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for step in report.get("steps", []):
        if step.get("status") != "failed":
            continue
        out.append(
            finding(
                finding_type="gate_failed",
                title=f"Gate failed: {step.get('command')}",
                source=source,
                severity=SEVERITY_BASE["gate_failed"],
                confidence=0.95,
                evidence=list(step.get("stderr_tail", [])) + list(step.get("stdout_tail", [])),
                next_actions=[step.get("command", "")],
            )
        )
    return out


def compare_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for match in report.get("matches", []):
        for gap in match.get("gaps", []):
            out.append(
                finding(
                    finding_type="compare_gap",
                    title=f"Mirror gap: {match.get('id')}",
                    source=source,
                    severity=SEVERITY_BASE["compare_gap"],
                    confidence=0.65,
                    evidence=[gap],
                    next_actions=list(match.get("materialization_commands", []))[:4],
                )
            )
        if match.get("id") == "uncovered_surface":
            out.append(
                finding(
                    finding_type="mirror_uncovered",
                    title="No mirror registered for requested surface",
                    source=source,
                    severity=SEVERITY_BASE["mirror_uncovered"],
                    confidence=0.85,
                    evidence=list(match.get("gaps", [])),
                    next_actions=list(match.get("commands", []))[:4],
                )
            )
    return out


def content_mirror_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for error in report.get("errors", []):
        out.append(
            finding(
                finding_type="ingest_error",
                title="Content mirror input error",
                source=source,
                severity=SEVERITY_BASE["ingest_error"],
                confidence=0.92,
                evidence=[error],
                next_actions=["Fix source paths and rerun `python -m tools.debugger content-mirror`."],
            )
        )
    if not report.get("invariant_count"):
        out.append(
            finding(
                finding_type="test_gap",
                title="Content mirror produced no invariants",
                source=source,
                severity=SEVERITY_BASE["test_gap"],
                confidence=0.6,
                evidence=["Provide --source-file or --changed-file for a map, script, gfx, audio, or data source."],
                next_actions=["python -m tools.debugger content-mirror --source-file <changed_file>"],
            )
        )
    for item in report.get("invariants", []):
        if not isinstance(item, dict) or item.get("status") not in {"failed", "warning"}:
            continue
        failed = item.get("status") == "failed"
        finding_type = "content_mirror_failed" if failed else "content_mirror_warning"
        out.append(
            finding(
                finding_type=finding_type,
                title=f"Content invariant {item.get('status')}: {item.get('title', item.get('id', '<unknown>'))}",
                source=source,
                severity=int(item.get("severity", SEVERITY_BASE[finding_type])),
                confidence=0.86 if failed else 0.68,
                evidence=list(item.get("evidence", []))[:4],
                next_actions=list(item.get("commands", []))[:4],
            )
        )
    return out


def content_scenario_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for error in report.get("errors", []):
        out.append(
            finding(
                finding_type="ingest_error",
                title="Content scenario input error",
                source=source,
                severity=SEVERITY_BASE["ingest_error"],
                confidence=0.92,
                evidence=[error],
                next_actions=["Fix source paths and rerun `python -m tools.debugger content-scenarios`."],
            )
        )
    if not report.get("scenario_count"):
        out.append(
            finding(
                finding_type="test_gap",
                title="Content scenario generator produced no scenarios",
                source=source,
                severity=SEVERITY_BASE["test_gap"],
                confidence=0.6,
                evidence=["Provide --source-file or --changed-file for a map, script, gfx, audio, or data source."],
                next_actions=["python -m tools.debugger content-scenarios --source-file <changed_file>"],
            )
        )
    for scenario in report.get("scenarios", [])[:30]:
        if not isinstance(scenario, dict):
            continue
        location = f"{scenario.get('source_file', '')}:{scenario.get('line', 0)}"
        out.append(
            finding(
                finding_type="content_scenario",
                title=f"Content scenario: {scenario.get('scenario_type', scenario.get('id', '<unknown>'))}",
                source=source,
                severity=SEVERITY_BASE["content_scenario"],
                confidence=0.72,
                evidence=[location, *string_items(scenario.get("expected"))[:3]],
                next_actions=content_scenario_commands(scenario)[:6],
            )
        )
    return out


def content_scenario_commands(scenario: dict[str, Any]) -> list[str]:
    commands = string_items(scenario.get("commands"))
    for probe in scenario.get("behavioral_probes", []):
        if isinstance(probe, dict):
            commands.extend(string_items(probe.get("command")))
    return unique_string_items(commands)


def content_state_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for error in report.get("errors", []):
        out.append(
            finding(
                finding_type="ingest_error",
                title="Content state materialization input error",
                source=source,
                severity=SEVERITY_BASE["ingest_error"],
                confidence=0.92,
                evidence=[error],
                next_actions=string_items(report.get("commands"))[:4]
                or ["python -m tools.debugger content-state --report <content-scenarios.json>"],
            )
        )
    materializations = dict_items(report.get("materializations"))
    if not materializations:
        out.append(
            finding(
                finding_type="test_gap",
                title="Content state materializer produced no patchable state",
                source=source,
                severity=SEVERITY_BASE["test_gap"],
                confidence=0.65,
                evidence=["Provide a content-scenarios report with map_position state_preconditions."],
                next_actions=string_items(report.get("commands"))[:4]
                or ["python -m tools.debugger content-state --report <content-scenarios.json>"],
            )
        )
    execution = report.get("execution") if isinstance(report.get("execution"), dict) else {}
    out_state = str(execution.get("out_state") or report.get("out_state") or "")
    report_commands = string_items(report.get("commands"))
    for materialization in materializations[:30]:
        status = str(materialization.get("status", "planned"))
        scenario_id = str(materialization.get("scenario_id", "") or materialization.get("precondition_id", ""))
        title_id = scenario_id or str(materialization.get("precondition_kind", "content state"))
        errors = string_items(materialization.get("errors"))
        notes = string_items(materialization.get("notes"))
        evidence = [
            f"scenario={scenario_id}" if scenario_id else "",
            f"status={status}",
            f"precondition={materialization.get('precondition_kind', '')}",
            f"source={materialization.get('source_file', '')}",
            f"map={materialization.get('map_name', '')}",
            *content_state_patch_evidence(materialization.get("patches")),
            *errors[:4],
            *notes[:4],
        ]
        commands = content_state_commands(
            source=source,
            materialization=materialization,
            out_state=out_state,
            report_commands=report_commands,
        )
        if status == "ready" and not errors:
            out.append(
                finding(
                    finding_type="content_state_ready",
                    title=f"Content state ready: {title_id}",
                    source=source,
                    severity=SEVERITY_BASE["content_state_ready"],
                    confidence=0.78,
                    evidence=evidence,
                    next_actions=commands[:8],
                )
            )
            continue
        severity = SEVERITY_BASE["content_state_blocked"] if errors or status == "blocked" else 52
        out.append(
            finding(
                finding_type="content_state_blocked",
                title=f"Content state {status}: {title_id}",
                source=source,
                severity=severity,
                confidence=0.82 if errors else 0.62,
                evidence=evidence,
                next_actions=commands[:8] or report_commands[:4],
            )
        )
    if bool(report.get("executed") or execution.get("executed")):
        applied_patches = dict_items(execution.get("applied_patches"))
        out.append(
            finding(
                finding_type="content_state_executed",
                title=f"Content state executed: {out_state or source}",
                source=source,
                severity=SEVERITY_BASE["content_state_executed"],
                confidence=0.86,
                evidence=[
                    f"out_state={out_state}",
                    f"applied_patches={len(applied_patches)}",
                    *content_state_patch_evidence(applied_patches),
                ],
                next_actions=content_state_execution_commands(
                    source=source,
                    materializations=materializations,
                    out_state=out_state,
                    applied_patches=applied_patches,
                )[:8],
            )
        )
    return out


def content_state_patch_evidence(raw_patches: Any) -> list[str]:
    out = []
    for patch in dict_items(raw_patches)[:8]:
        symbol = str(patch.get("symbol", ""))
        if not symbol:
            continue
        value = content_state_patch_value(patch)
        address = str(patch.get("bank_address") or patch.get("address") or "")
        suffix = f" @{address}" if address else ""
        out.append(f"patch {symbol}={value}{suffix}")
    return out


def content_state_patch_symbols(raw_patches: Any) -> list[str]:
    return unique_string_items(
        [
            str(patch.get("symbol", ""))
            for patch in dict_items(raw_patches)
            if patch.get("symbol")
        ]
    )


def content_state_patch_value(patch: dict[str, Any]) -> str:
    value_hex = str(patch.get("value_hex") or "")
    if value_hex:
        return f"0x{value_hex}"
    if patch.get("value") is not None:
        return str(patch.get("value"))
    return "<unknown>"


def content_state_commands(
    *,
    source: str,
    materialization: dict[str, Any],
    out_state: str,
    report_commands: list[str],
) -> list[str]:
    scenario_id = str(materialization.get("scenario_id", ""))
    commands = []
    for patch in dict_items(materialization.get("patches"))[:8]:
        symbol = str(patch.get("symbol", ""))
        if not symbol:
            continue
        value_hex = str(patch.get("value_hex") or "")
        value = patch.get("value")
        value_arg = f",value=0x{value_hex}" if value_hex else (f",value={value}" if value is not None else "")
        scenario_arg = f",scenario={scenario_id}" if scenario_id else ""
        commands.append(
            f"python -m tools.debugger expect --report {source} --expect state-patch={symbol}{scenario_arg}{value_arg}"
        )
    if scenario_id:
        commands.append(f"python -m tools.debugger replay --report {source} --scenario-id {scenario_id} --execute-watch")
    watch_command = content_state_watch_command(
        out_state=out_state,
        patch_symbols=[
            str(patch.get("symbol", ""))
            for patch in dict_items(materialization.get("patches"))
            if patch.get("symbol")
        ],
    )
    commands.extend(watch_command)
    commands.extend(string_items(materialization.get("commands")))
    commands.extend(report_commands)
    return unique_string_items(commands)


def content_state_execution_commands(
    *,
    source: str,
    materializations: list[dict[str, Any]],
    out_state: str,
    applied_patches: list[dict[str, Any]],
) -> list[str]:
    commands = [
        f"python -m tools.debugger replay --report {source} --scenario-id {scenario_id} --execute-watch"
        for scenario_id in unique_string_items(
            [
                str(materialization.get("scenario_id", ""))
                for materialization in materializations
                if materialization.get("scenario_id")
            ]
        )[:8]
    ]
    commands.extend(
        content_state_watch_command(
            out_state=out_state,
            patch_symbols=[
                str(patch.get("symbol", ""))
                for patch in applied_patches
                if patch.get("symbol")
            ],
        )
    )
    return unique_string_items(commands)


def content_state_watch_command(*, out_state: str, patch_symbols: list[str]) -> list[str]:
    symbols = unique_string_items([symbol for symbol in patch_symbols if symbol])[:6]
    if not out_state or not symbols:
        return []
    return [
        "python -m tools.debugger watch "
        + " ".join(f"--watch-symbol {symbol}" for symbol in symbols)
        + f" --save-state {out_state} --execute"
    ]


def state_space_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    report_commands = string_items(report.get("commands"))
    state_space = report.get("state_space") if isinstance(report.get("state_space"), dict) else {}
    execution = report.get("execution") if isinstance(report.get("execution"), dict) else {}
    patches = state_space_patch_records(report)
    scenario_ids = state_space_scenario_ids(report)
    source_files = state_space_source_files(report)
    out_state = str(execution.get("out_state") or report.get("out_state") or state_space.get("out_state") or "")
    errors = string_items(report.get("errors"))
    for error in errors:
        out.append(
            finding(
                finding_type="ingest_error",
                title="State-space materialization input error",
                source=source,
                severity=SEVERITY_BASE["ingest_error"],
                confidence=0.92,
                evidence=[error],
                next_actions=report_commands[:6]
                or ["python -m tools.debugger state-space --patch <symbol>=<value>"],
            )
        )
    if not patches:
        out.append(
            finding(
                finding_type="test_gap",
                title="State-space materializer produced no WRAM patches",
                source=source,
                severity=SEVERITY_BASE["test_gap"],
                confidence=0.65,
                evidence=["Provide at least one --patch SYMBOL=VALUE input."],
                next_actions=report_commands[:6]
                or ["python -m tools.debugger state-space --patch <symbol>=<value>"],
            )
        )
    elif errors or not report.get("valid", True):
        out.append(
            finding(
                finding_type="state_space_blocked",
                title="State-space blocked",
                source=source,
                severity=SEVERITY_BASE["state_space_blocked"],
                confidence=0.82,
                evidence=[*state_space_evidence(report), *errors[:4]],
                next_actions=report_commands[:8],
            )
        )
    else:
        title_id = scenario_ids[0] if scenario_ids else source
        out.append(
            finding(
                finding_type="state_space_ready",
                title=f"State-space ready: {title_id}",
                source=source,
                severity=SEVERITY_BASE["state_space_ready"],
                confidence=0.78,
                evidence=state_space_evidence(report),
                next_actions=state_space_commands(
                    source=source,
                    scenario_ids=scenario_ids,
                    out_state=out_state,
                    patches=patches,
                    report_commands=report_commands,
                )[:8],
            )
        )
    if bool(report.get("executed") or execution.get("executed")):
        applied_patches = dict_items(execution.get("applied_patches")) or [patch for patch in patches if patch.get("applied")]
        out.append(
            finding(
                finding_type="state_space_executed",
                title=f"State-space executed: {out_state or source}",
                source=source,
                severity=SEVERITY_BASE["state_space_executed"],
                confidence=0.86,
                evidence=[
                    f"out_state={out_state}",
                    f"applied_patches={len(applied_patches)}",
                    *content_state_patch_evidence(applied_patches),
                ],
                next_actions=state_space_commands(
                    source=source,
                    scenario_ids=scenario_ids,
                    out_state=out_state,
                    patches=applied_patches or patches,
                    report_commands=report_commands,
                )[:8],
            )
        )
    return out


def state_space_patch_records(report: dict[str, Any]) -> list[dict[str, Any]]:
    state_space = report.get("state_space") if isinstance(report.get("state_space"), dict) else {}
    execution = report.get("execution") if isinstance(report.get("execution"), dict) else {}
    return [
        *dict_items(report.get("state_patches")),
        *dict_items(state_space.get("patches")),
        *dict_items(state_space.get("state_patches")),
        *dict_items(execution.get("applied_patches")),
    ]


def state_space_scenario_ids(report: dict[str, Any]) -> list[str]:
    state_space = report.get("state_space") if isinstance(report.get("state_space"), dict) else {}
    return unique_string_items(
        [
            str(report.get("scenario_id", "")),
            *string_items(state_space.get("scenario_ids")),
            *[
                str(patch.get("scenario_id", ""))
                for patch in state_space_patch_records(report)
                if patch.get("scenario_id")
            ],
        ]
    )


def state_space_source_files(report: dict[str, Any]) -> list[str]:
    state_space = report.get("state_space") if isinstance(report.get("state_space"), dict) else {}
    return unique_string_items(
        [
            *string_items(report.get("source_files")),
            *string_items(state_space.get("source_files")),
            *[
                str(patch.get("source_file", ""))
                for patch in state_space_patch_records(report)
                if patch.get("source_file")
            ],
        ]
    )


def state_space_evidence(report: dict[str, Any]) -> list[str]:
    state_space = report.get("state_space") if isinstance(report.get("state_space"), dict) else {}
    return [
        f"scenario={','.join(state_space_scenario_ids(report))}" if state_space_scenario_ids(report) else "",
        f"source={','.join(state_space_source_files(report))}" if state_space_source_files(report) else "",
        f"patches={len(state_space_patch_records(report))}",
        f"symptom={report.get('symptom') or state_space.get('symptom') or ''}",
        *content_state_patch_evidence(state_space_patch_records(report)),
    ]


def state_space_commands(
    *,
    source: str,
    scenario_ids: list[str],
    out_state: str,
    patches: list[dict[str, Any]],
    report_commands: list[str],
) -> list[str]:
    commands = []
    scenario_id = scenario_ids[0] if scenario_ids else ""
    scenario_expect_arg = f",scenario={scenario_id}" if scenario_id else ""
    scenario_cli_arg = f" --scenario-id {scenario_id}" if scenario_id else ""
    for patch in patches[:8]:
        symbol = str(patch.get("symbol", ""))
        if not symbol:
            continue
        value_hex = str(patch.get("value_hex") or "")
        value = patch.get("value")
        value_arg = f",value=0x{value_hex}" if value_hex else (f",value={value}" if value is not None else "")
        commands.append(
            f"python -m tools.debugger expect --report {source} --expect state-patch={symbol}{scenario_expect_arg}{value_arg}"
        )
    commands.append(f"python -m tools.debugger replay --report {source}{scenario_cli_arg} --execute-watch")
    commands.extend(content_state_watch_command(out_state=out_state, patch_symbols=content_state_patch_symbols(patches)))
    commands.append(
        f"python -m tools.debugger trace-instructions --report {source}{scenario_cli_arg} --execute --require-hit"
    )
    commands.append(
        f"python -m tools.debugger minimize --report {source} --expect state-patch={content_state_patch_symbols(patches)[0] if content_state_patch_symbols(patches) else '<symbol>'} --out-state-report .local\\tmp\\debugger_state_space_minimized.json"
    )
    commands.extend(report_commands)
    return unique_string_items(commands)


def expectation_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for error in report.get("errors", []):
        out.append(
            finding(
                finding_type="ingest_error",
                title="Expectation input error",
                source=source,
                severity=SEVERITY_BASE["ingest_error"],
                confidence=0.95,
                evidence=[error],
                next_actions=["Fix expectation inputs and rerun `python -m tools.debugger expect`."],
            )
        )
    if not report.get("expectation_count"):
        out.append(
            finding(
                finding_type="test_gap",
                title="No behavior expectations were provided",
                source=source,
                severity=SEVERITY_BASE["test_gap"],
                confidence=0.65,
                evidence=["Add --expect, --expect-file, --symbol, --event, --rule, --address, or --source-file."],
                next_actions=["python -m tools.debugger expect --expect no-errors --report <report.json>"],
            )
        )
    for item in report.get("expectations", []):
        if not isinstance(item, dict) or item.get("status") != "failed":
            continue
        out.append(
            finding(
                finding_type="expectation_failed",
                title=f"Expectation failed: {item.get('id')}",
                source=source,
                severity=int(item.get("severity", SEVERITY_BASE["expectation_failed"])),
                confidence=0.88,
                evidence=list(item.get("evidence", []))[:4] or [
                    f"observed_count={item.get('observed_count', 0)} min_count={item.get('min_count', 1)}"
                ],
                next_actions=list(item.get("commands", []))[:4],
            )
        )
    return out


def test_suggestion_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for match in report.get("matches", []):
        for note in match.get("notes", []):
            if "still needs" not in note and "No focused generator" not in note:
                continue
            out.append(
                finding(
                    finding_type="test_gap",
                    title=f"Generator gap: {match.get('id')}",
                    source=source,
                    severity=SEVERITY_BASE["test_gap"],
                    confidence=0.65,
                    evidence=[note],
                    next_actions=list(match.get("commands", []))[:4],
                )
            )
    return out


def provenance_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for warning in report.get("warnings", []):
        out.append(
            finding(
                finding_type="provenance_warning",
                title="Provenance warning",
                source=source,
                severity=SEVERITY_BASE["provenance_warning"],
                confidence=0.7,
                evidence=[warning],
                next_actions=["Check symbol names and source paths."],
            )
        )
    for symbol in report.get("symbols", []):
        for warning in symbol.get("warnings", []):
            out.append(
                finding(
                    finding_type="provenance_warning",
                    title=f"Provenance warning: {symbol.get('query')}",
                    source=source,
                    severity=SEVERITY_BASE["provenance_warning"],
                    confidence=0.7,
                    evidence=[warning],
                    next_actions=["Check symbol spelling or rebuild the .sym file."],
                )
            )
    return out


def slice_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for error in report.get("errors", []):
        out.append(
            finding(
                finding_type="ingest_error",
                title="Causal slice setup error",
                source=source,
                severity=SEVERITY_BASE["ingest_error"],
                confidence=0.95,
                evidence=[error],
                next_actions=["Fix slice inputs and rerun `python -m tools.debugger slice`."],
            )
        )
    for warning in report.get("warnings", []):
        out.append(
            finding(
                finding_type="provenance_warning",
                title="Causal slice warning",
                source=source,
                severity=SEVERITY_BASE["provenance_warning"],
                confidence=0.7,
                evidence=[warning],
                next_actions=["Check symbol spelling or rebuild the .sym file."],
            )
        )
    return out


def taint_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for error in report.get("errors", []):
        out.append(
            finding(
                finding_type="ingest_error",
                title="Taint setup error",
                source=source,
                severity=SEVERITY_BASE["ingest_error"],
                confidence=0.9,
                evidence=[error],
                next_actions=["Fix taint inputs and rerun `python -m tools.debugger taint --symbol <symbol>`."],
            )
        )
    for warning in report.get("warnings", []):
        out.append(
            finding(
                finding_type="provenance_warning",
                title="Taint warning",
                source=source,
                severity=SEVERITY_BASE["provenance_warning"],
                confidence=0.7,
                evidence=[warning],
                next_actions=["Check symbol spelling, source filters, or rebuild the .sym file."],
            )
        )
    for path in report.get("paths", [])[:20]:
        if not isinstance(path, dict):
            continue
        out.append(
            finding(
                finding_type="taint_path",
                title=f"Taint path: {path.get('title', '<unknown>')}",
                source=source,
                severity=min(90, max(SEVERITY_BASE["taint_path"], int(path.get("score", 0)))),
                confidence=float(path.get("confidence", 0.6)),
                evidence=list(path.get("evidence", []))[:4],
                next_actions=list(path.get("commands", []))[:4],
            )
        )
    for attribution in report.get("write_attributions", [])[:20]:
        if not isinstance(attribution, dict):
            continue
        out.append(
            finding(
                finding_type="reverse_attribution",
                title=f"Dynamic write: {attribution.get('target', '<sink>')} at {attribution.get('pc_label', '<pc>')}",
                source=source,
                severity=min(92, max(SEVERITY_BASE["reverse_attribution"], int(attribution.get("score", 0)))),
                confidence=float(attribution.get("confidence", 0.72)),
                evidence=list(attribution.get("evidence", []))[:5],
                next_actions=list(attribution.get("commands", []))[:5],
            )
        )
    return out


def instruction_trace_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for error in report.get("errors", []):
        if is_instruction_trace_validation_error(str(error)):
            continue
        out.append(
            finding(
                finding_type="ingest_error",
                title="Instruction trace setup error",
                source=source,
                severity=SEVERITY_BASE["ingest_error"],
                confidence=0.9,
                evidence=[error],
                next_actions=["Fix trace-instructions inputs and rerun `python -m tools.debugger trace-instructions`."],
            )
        )
    validation = report.get("execution_validation") if isinstance(report.get("execution_validation"), dict) else {}
    trace_path = instruction_trace_output_path(report)
    if validation.get("attempted") and not validation.get("hit"):
        out.append(
            finding(
                finding_type="instruction_trace_miss",
                title="Instruction trace executed but selected hooks did not fire",
                source=source,
                severity=SEVERITY_BASE["instruction_trace_miss"] + (6 if validation.get("required") else 0),
                confidence=0.88,
                evidence=instruction_trace_validation_evidence(report, validation),
                next_actions=string_items(report.get("commands"))[:6]
                or ["python -m tools.debugger setup --report <instruction_trace.json>"],
            )
        )
    missing_functions = string_items(validation.get("missing_function_symbols"))
    if validation.get("attempted") and validation.get("hit") and missing_functions:
        out.append(
            finding(
                finding_type="instruction_trace_partial",
                title="Instruction trace missed some selected routines",
                source=source,
                severity=SEVERITY_BASE["instruction_trace_partial"],
                confidence=0.82,
                evidence=instruction_trace_validation_evidence(report, validation),
                next_actions=string_items(report.get("commands"))[:6],
            )
        )
    if validation.get("trace_record_limit_hit"):
        out.append(
            finding(
                finding_type="instruction_trace_limit",
                title="Instruction trace reached the record limit",
                source=source,
                severity=SEVERITY_BASE["instruction_trace_limit"],
                confidence=0.82,
                evidence=instruction_trace_validation_evidence(report, validation),
                next_actions=instruction_trace_limit_commands(report, trace_path=trace_path),
            )
        )
    if validation.get("ready_for_dynamic_taint"):
        out.append(
            finding(
                finding_type="instruction_trace_ready",
                title="Instruction trace is ready for dynamic taint",
                source=source,
                severity=SEVERITY_BASE["instruction_trace_ready"],
                confidence=0.86,
                evidence=instruction_trace_validation_evidence(report, validation),
                next_actions=instruction_trace_dynamic_taint_commands(report, validation, trace_path=trace_path),
            )
        )
    for function in report.get("functions", [])[:12]:
        if not isinstance(function, dict):
            continue
        out.append(
            finding(
                finding_type="trace_event",
                title=f"Instruction trace planned: {function.get('symbol', '<function>')}",
                source=source,
                severity=58,
                confidence=0.78,
                evidence=[
                    f"instructions={function.get('instruction_count', 0)}",
                    f"hooks={function.get('hook_count', 0)}",
                ],
                next_actions=list(report.get("commands", []))[:4],
            )
        )
    return out


def is_instruction_trace_validation_error(error: str) -> bool:
    lowered = error.lower()
    return (
        "instruction trace executed but none of the selected hooks fired" in lowered
        or "instruction trace did not hit every selected function" in lowered
        or "instruction trace reached --max-frames" in lowered
    )


def instruction_trace_validation_evidence(report: dict[str, Any], validation: dict[str, Any]) -> list[str]:
    return [
        f"attempted={validation.get('attempted')}",
        f"required={validation.get('required')}",
        f"hit={validation.get('hit')}",
        f"captured_frames={validation.get('captured_frame_count', report.get('captured_frame_count', 0))}",
        f"planned_hooks={validation.get('planned_hook_count', 0)}",
        f"hit_functions={','.join(string_items(validation.get('hit_function_symbols'))[:8])}",
        f"missing_functions={','.join(string_items(validation.get('missing_function_symbols'))[:8])}",
        f"watch_symbols={','.join(string_items(validation.get('watch_symbols'))[:8])}",
        f"trace={instruction_trace_output_path(report)}",
        f"save_state={report.get('effective_save_state') or report.get('save_state', '')}",
        *string_items(report.get("warnings"))[:4],
    ]


def instruction_trace_output_path(report: dict[str, Any]) -> str:
    trace_output = report.get("trace_output") if isinstance(report.get("trace_output"), dict) else {}
    return str(trace_output.get("path") or "")


def instruction_trace_dynamic_taint_commands(
    report: dict[str, Any],
    validation: dict[str, Any],
    *,
    trace_path: str,
) -> list[str]:
    commands = []
    if trace_path:
        commands.append(f"python -m tools.debugger trace-index --trace {trace_path}")
        commands.append(f"python -m tools.debugger minimize --trace {trace_path} --expect event=control_flow")
        for watch in string_items(validation.get("watch_symbols"))[:4]:
            commands.append(
                f"python -m tools.debugger dynamic-taint --trace {trace_path} --sink-symbol {watch} --source-reg <register-or-origin>"
            )
            commands.append(f"python -m tools.debugger expect --trace {trace_path} --expect contains={watch}")
    commands.extend(string_items(report.get("commands"))[:4])
    return unique_string_items(commands)


def instruction_trace_limit_commands(report: dict[str, Any], *, trace_path: str) -> list[str]:
    commands = []
    if trace_path:
        commands.append(f"python -m tools.debugger trace-index --trace {trace_path}")
    commands.extend(
        command.replace("--max-frames 50000", "--max-frames 100000")
        for command in string_items(report.get("commands"))[:4]
    )
    return unique_string_items(commands)


def explanation_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for error in report.get("errors", []):
        out.append(
            finding(
                finding_type="ingest_error",
                title="Causal explanation setup error",
                source=source,
                severity=SEVERITY_BASE["ingest_error"],
                confidence=0.9,
                evidence=[error],
                next_actions=["Fix explanation inputs and rerun `python -m tools.debugger explain`."],
            )
        )
    if not report.get("paths"):
        out.append(
            finding(
                finding_type="provenance_warning",
                title="No causal explanation paths were produced",
                source=source,
                severity=SEVERITY_BASE["provenance_warning"],
                confidence=0.7,
                evidence=list(report.get("warnings", []))[:4],
                next_actions=["python -m tools.debugger explain --report <watch-or-replay-report.json>"],
            )
        )
    for path in report.get("paths", [])[:20]:
        if not isinstance(path, dict):
            continue
        score = int(path.get("score", 0))
        if score < 70:
            continue
        out.append(
            finding(
                finding_type="causal_path",
                title=f"Causal path: {path.get('title', '<unknown>')}",
                source=source,
                severity=min(95, score),
                confidence=float(path.get("confidence", 0.6)),
                evidence=list(path.get("evidence", []))[:4],
                next_actions=list(path.get("commands", []))[:4],
            )
        )
    return out


def localization_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for error in report.get("errors", []):
        out.append(
            finding(
                finding_type="ingest_error",
                title="Localization setup error",
                source=source,
                severity=SEVERITY_BASE["ingest_error"],
                confidence=0.95,
                evidence=[error],
                next_actions=["Fix localization inputs and rerun `python -m tools.debugger localize`."],
            )
        )
    if not report.get("candidates"):
        out.append(
            finding(
                finding_type="test_gap",
                title="No localization candidates were produced",
                source=source,
                severity=SEVERITY_BASE["test_gap"],
                confidence=0.6,
                evidence=["Provide a symptom, symbol, changed file, or unified JSON report."],
                next_actions=["python -m tools.debugger localize --symptom <description> --symbol <watch_symbol>"],
            )
        )
    return out


def coverage_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for error in report.get("errors", []):
        out.append(
            finding(
                finding_type="ingest_error",
                title="Coverage setup error",
                source=source,
                severity=SEVERITY_BASE["ingest_error"],
                confidence=0.95,
                evidence=[error],
                next_actions=["Fix coverage inputs and rerun `python -m tools.debugger coverage`."],
            )
        )
    for target in report.get("uncovered_targets", []):
        out.append(
            finding(
                finding_type="coverage_gap",
                title=f"Coverage gap: {target.get('type')} {target.get('id')}",
                source=source,
                severity=SEVERITY_BASE["coverage_gap"],
                confidence=0.7,
                evidence=["target was not directly or indirectly observed in provided traces/reports"],
                next_actions=list(target.get("commands", []))[:4],
            )
        )
    return out


def trace_index_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for error in report.get("errors", []):
        out.append(
            finding(
                finding_type="ingest_error",
                title="Trace index setup error",
                source=source,
                severity=SEVERITY_BASE["ingest_error"],
                confidence=0.95,
                evidence=[error],
                next_actions=["Fix trace inputs and rerun `python -m tools.debugger trace-index`."],
            )
        )
    if not report.get("matched_event_count", 0):
        out.append(
            finding(
                finding_type="coverage_gap",
                title="Trace index found no matching events",
                source=source,
                severity=SEVERITY_BASE["coverage_gap"],
                confidence=0.62,
                evidence=["No trace events matched the requested symbols, addresses, rules, source files, or symptom."],
                next_actions=["python -m tools.debugger trace-index --trace <trace.json> --symbol <symbol>"],
            )
        )
    for event in report.get("events", [])[:30]:
        if not isinstance(event, dict):
            continue
        event_type = str(event.get("event_type", "trace_event"))
        if event_type not in {"watch_change", "score_delta", "memory_write", "memory_patch"}:
            continue
        state = event.get("state_symbol") or event.get("bank_address") or event.get("address") or "state"
        source_symbol = event.get("source_symbol") or event.get("pc_symbol") or event.get("rule_id") or "trace"
        out.append(
            finding(
                finding_type="trace_event",
                title=f"Trace event: {state} {event_type} from {source_symbol}",
                source=source,
                severity=70 if event_type == "watch_change" else 64,
                confidence=float(event.get("confidence", 0.7)),
                evidence=list(event.get("evidence", []))[:4],
                next_actions=list(event.get("commands", []))[:4] or event_commands(event),
            )
        )
    for path in report.get("causal_paths", [])[:20]:
        if not isinstance(path, dict):
            continue
        if int(path.get("score", 0)) < 70:
            continue
        out.append(
            finding(
                finding_type="causal_path",
                title=f"Trace causal path: {path.get('title', '<unknown>')}",
                source=source,
                severity=min(95, int(path.get("score", 0))),
                confidence=float(path.get("confidence", 0.65)),
                evidence=list(path.get("evidence", []))[:4],
                next_actions=list(path.get("commands", []))[:4],
            )
        )
    for item in report.get("reverse_attributions", [])[:20]:
        if not isinstance(item, dict):
            continue
        out.append(
            finding(
                finding_type="reverse_attribution",
                title=f"Reverse attribution: {item.get('title', '<unknown>')}",
                source=source,
                severity=72,
                confidence=float(item.get("confidence", 0.65)),
                evidence=list(item.get("evidence", []))[:4],
                next_actions=list(item.get("commands", []))[:4],
            )
        )
    return out


def event_commands(event: dict[str, Any]) -> list[str]:
    commands = []
    for symbol in (event.get("state_symbol"), event.get("source_symbol"), event.get("pc_symbol")):
        if symbol:
            commands.append(f"python -m tools.debugger explain --symbol {symbol}")
    if event.get("address"):
        commands.append(f"python -m tools.debugger trace-index --address {event.get('address')}")
    if event.get("rule_id"):
        commands.append(f"python -m tools.debugger coverage --rule {event.get('rule_id')}")
    return commands


def group_status(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("status", ""))
    return str(value or "")


def next_step_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    recommendation = report.get("recommendation") if isinstance(report.get("recommendation"), dict) else {}
    if not recommendation:
        return [
            finding(
                finding_type="test_gap",
                title="Next-step report has no recommendation",
                source=source,
                severity=SEVERITY_BASE["test_gap"],
                confidence=0.7,
                evidence=["rerun `python -m tools.debugger next` with a symptom or changed file"],
                next_actions=["python -m tools.debugger next --symptom <description>"],
            )
        ]

    first_command = str(recommendation.get("first_command") or "")
    regression_gate = str(recommendation.get("regression_gate") or "")
    escalation_command = str(recommendation.get("escalation_command") or "")
    required_inputs = string_items(recommendation.get("required_inputs"))
    source_refs = string_items(recommendation.get("source_refs"))
    evidence_standard = string_items(recommendation.get("evidence_standard"))
    disproof_standard = string_items(recommendation.get("disproof_standard"))
    evidence = [
        f"matched_lane={report.get('matched_lane', recommendation.get('matched_lane', ''))}",
        f"symptom_class={recommendation.get('symptom_class', '')}",
        f"symptom={report.get('symptom', '')}",
        *[f"required_input={item}" for item in required_inputs[:4]],
        *[f"source_ref={item}" for item in source_refs[:4]],
        *[f"evidence_standard={item}" for item in evidence_standard[:4]],
        *[f"disproof_standard={item}" for item in disproof_standard[:4]],
        f"proof_limit={recommendation.get('proof_limit', '')}",
        f"regression_gate={regression_gate}",
    ]
    next_actions = unique_string_items([first_command, regression_gate, escalation_command])
    for recipe in string_items(recommendation.get("repro_recipes"))[:3]:
        next_actions.append(f"python -m tools.debugger repro-recipe --id {recipe}")

    return [
        finding(
            finding_type="next_step",
            title=f"Next proof path: {recommendation.get('title', recommendation.get('symptom_class', '<unknown>'))}",
            source=source,
            severity=SEVERITY_BASE["next_step"],
            confidence=0.82,
            evidence=evidence,
            next_actions=next_actions[:6],
        )
    ]


def minimization_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for error in report.get("errors", []):
        out.append(
            finding(
                finding_type="ingest_error",
                title="Minimization setup error",
                source=source,
                severity=SEVERITY_BASE["ingest_error"],
                confidence=0.95,
                evidence=[error],
                next_actions=["Fix minimization inputs and rerun `python -m tools.debugger minimize`."],
            )
        )
    if not report.get("steps"):
        out.append(
            finding(
                finding_type="test_gap",
                title="No minimization route was produced",
                source=source,
                severity=SEVERITY_BASE["test_gap"],
                confidence=0.65,
                evidence=["Provide a scenario, report, symbol, bug id, changed file, or symptom."],
                next_actions=["python -m tools.debugger minimize --report <report.json> --scenario <scenarios.jsonl>"],
            )
        )
    evidence_minimization = report.get("evidence_minimization")
    if isinstance(evidence_minimization, dict) and evidence_minimization.get("attempted"):
        if evidence_minimization.get("preserved"):
            out.append(
                finding(
                    finding_type="minimization_route",
                    title="Generic evidence minimized",
                    source=source,
                    severity=60,
                    confidence=0.78,
                    evidence=[
                        f"{evidence_minimization.get('original_count', 0)} -> {evidence_minimization.get('minimized_count', 0)} records",
                        f"context frames: {evidence_minimization.get('context_frame_original_count', 0)} -> {evidence_minimization.get('context_frame_minimized_count', 0)}",
                        f"artifact: {evidence_minimization.get('out_trace', '')}",
                    ],
                    next_actions=[
                        f"python -m tools.debugger trace-index --trace {evidence_minimization.get('out_trace')}",
                        f"python -m tools.debugger expect --trace {evidence_minimization.get('out_trace')} --expect <expectation>",
                    ],
                )
            )
        else:
            out.append(
                finding(
                    finding_type="test_gap",
                    title="Generic evidence minimization did not preserve expectations",
                    source=source,
                    severity=SEVERITY_BASE["test_gap"],
                    confidence=0.72,
                    evidence=list(evidence_minimization.get("errors", []))[:4]
                    or [str(evidence_minimization.get("reason", ""))],
                    next_actions=["python -m tools.debugger minimize --trace <trace.json> --expect <expectation> --out-trace <minimized.json>"],
                )
            )
    state_patch_minimization = report.get("state_patch_minimization")
    if isinstance(state_patch_minimization, dict) and state_patch_minimization.get("attempted"):
        if state_patch_minimization.get("preserved"):
            out.append(
                finding(
                    finding_type="minimization_route",
                    title="Content state patches minimized",
                    source=source,
                    severity=61,
                    confidence=0.8,
                    evidence=[
                        f"{state_patch_minimization.get('original_patch_count', 0)} -> {state_patch_minimization.get('minimized_patch_count', 0)} patches",
                        f"artifact: {state_patch_minimization.get('out_report', '')}",
                        *string_items(state_patch_minimization.get("symbols"))[:4],
                    ],
                    next_actions=string_items(state_patch_minimization.get("commands"))[:6],
                )
            )
        else:
            out.append(
                finding(
                    finding_type="test_gap",
                    title="Content state patch minimization did not preserve expectations",
                    source=source,
                    severity=SEVERITY_BASE["test_gap"],
                    confidence=0.72,
                    evidence=string_items(state_patch_minimization.get("errors"))[:4]
                    or [str(state_patch_minimization.get("reason", ""))],
                    next_actions=["python -m tools.debugger minimize --report <content_state.json> --expect state-patch=<symbol> --out-state-report <minimized_content_state.json>"],
                )
            )
    return out


def generation_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for error in report.get("errors", []):
        out.append(
            finding(
                finding_type="ingest_error",
                title="Generation setup error",
                source=source,
                severity=SEVERITY_BASE["ingest_error"],
                confidence=0.95,
                evidence=[error],
                next_actions=["Fix generation inputs and rerun `python -m tools.debugger generate`."],
            )
        )
    if not report.get("generators"):
        out.append(
            finding(
                finding_type="test_gap",
                title="No generation route was produced",
                source=source,
                severity=SEVERITY_BASE["test_gap"],
                confidence=0.65,
                evidence=["Provide a symptom, symbol, changed file, report, scenario, or family."],
                next_actions=["python -m tools.debugger generate --symptom <description>"],
            )
        )
    for generator in report.get("generators", []):
        if not isinstance(generator, dict):
            continue
        commands = generation_commands(generator)
        status = str(generator.get("status", ""))
        if status == "ready":
            out.append(
                finding(
                    finding_type="generation_route",
                    title=f"Generator route: {generator.get('id')}",
                    source=source,
                    severity=58,
                    confidence=float(generator.get("confidence", 0.7)),
                    evidence=[
                        f"surface: {generator.get('surface', '')}",
                        f"seed ids: {len(generator.get('seed_ids', []))}",
                    ],
                    next_actions=commands[:4],
                )
            )
            continue
        out.append(
            finding(
                finding_type="test_gap",
                title=f"Generator gap: {generator.get('id')}",
                source=source,
                severity=SEVERITY_BASE["test_gap"],
                confidence=float(generator.get("confidence", 0.55)),
                evidence=list(generator.get("gaps", []))[:4] or [f"status: {status}"],
                next_actions=commands[:4],
            )
        )
    for limit in report.get("known_limits", []):
        out.append(
            finding(
                finding_type="test_gap",
                title="Generation plan limitation",
                source=source,
                severity=35,
                confidence=0.7,
                evidence=[str(limit)],
                next_actions=list(report.get("commands", []))[:4],
            )
        )
    return out


def generation_commands(generator: dict[str, Any]) -> list[str]:
    out = []
    for key in ("commands", "counterexample_commands", "materialization_commands"):
        for item in generator.get(key, []):
            if isinstance(item, dict):
                out.append(str(item.get("command", "")))
            elif isinstance(item, str):
                out.append(item)
    return [item for item in out if item]


def fuzz_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for error in report.get("errors", []):
        out.append(
            finding(
                finding_type="ingest_error",
                title="Fuzz setup error",
                source=source,
                severity=SEVERITY_BASE["ingest_error"],
                confidence=0.95,
                evidence=[error],
                next_actions=["Fix fuzz inputs and rerun `python -m tools.debugger fuzz`."],
            )
        )
    if not report.get("campaigns"):
        out.append(
            finding(
                finding_type="test_gap",
                title="No fuzz campaign was produced",
                source=source,
                severity=SEVERITY_BASE["test_gap"],
                confidence=0.65,
                evidence=["Provide a symptom, symbol, changed file, report, scenario, or family."],
                next_actions=["python -m tools.debugger fuzz --symptom <description>"],
            )
        )
    for campaign in report.get("campaigns", []):
        if not isinstance(campaign, dict):
            continue
        proof_level = str(campaign.get("proof_level", "planning"))
        status = str(campaign.get("status", "planned"))
        severity = SEVERITY_BASE["fuzz_campaign"] if proof_level == "dynamic" else SEVERITY_BASE["test_gap"]
        finding_type = "fuzz_campaign" if proof_level == "dynamic" else "test_gap"
        out.append(
            finding(
                finding_type=finding_type,
                title=f"Fuzz campaign: {campaign.get('id')}",
                source=source,
                severity=severity,
                confidence=float(campaign.get("confidence", 0.55)),
                evidence=[
                    f"surface: {campaign.get('surface', '')}",
                    f"proof_level: {proof_level}",
                    f"status: {status}",
                    *list(campaign.get("gaps", []))[:2],
                ],
                next_actions=list(campaign.get("commands", []))[:4],
            )
        )
    for case in report.get("fuzz_cases", [])[:20]:
        if not isinstance(case, dict):
            continue
        if case.get("proof_level") == "dynamic":
            continue
        out.append(
            finding(
                finding_type="test_gap",
                title=f"Static fuzz case: {case.get('id')}",
                source=source,
                severity=38,
                confidence=0.62,
                evidence=list(case.get("expectations", []))[:4] or list(case.get("notes", []))[:4],
                next_actions=list(case.get("commands", []))[:4],
            )
        )
    return out


def impact_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for item in report.get("items", [])[:40]:
        if not isinstance(item, dict):
            continue
        impact_score = int(item.get("impact_score", 0))
        if impact_score < 60:
            continue
        out.append(
            finding(
                finding_type="impact_hotspot",
                title=f"I{impact_score} {item.get('title', 'Impact item')}",
                source=source,
                severity=max(impact_score, int(item.get("severity", 0))),
                confidence=float(item.get("confidence", 0.6)),
                evidence=list(item.get("evidence", []))[:4],
                next_actions=list(item.get("next_actions", []))[:4],
            )
        )
    return out


def visualization_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for error in report.get("errors", []):
        out.append(
            finding(
                finding_type="ingest_error",
                title="Visualization input error",
                source=source,
                severity=SEVERITY_BASE["ingest_error"],
                confidence=0.9,
                evidence=[error],
                next_actions=["Fix visualization inputs and rerun `python -m tools.debugger visualize`."],
            )
        )
    for item in report.get("timeline", [])[:40]:
        if not isinstance(item, dict):
            continue
        severity = int(item.get("severity", 0))
        if severity < 70:
            continue
        out.append(
            finding(
                finding_type=f"visual_{item.get('lane', 'event')}",
                title=str(item.get("title", "Visualization event")),
                source=source,
                severity=severity,
                confidence=0.65,
                evidence=[str(item.get("detail", "")), str(item.get("source", ""))],
                next_actions=[],
            )
        )
    if not report.get("timeline_event_count") and not report.get("graph_node_count"):
        out.append(
            finding(
                finding_type="provenance_warning",
                title="Visualization produced no timeline or graph data",
                source=source,
                severity=SEVERITY_BASE["provenance_warning"],
                confidence=0.6,
                evidence=list(report.get("warnings", []))[:4],
                next_actions=["python -m tools.debugger visualize --report <report.json>"],
            )
        )
    return out


def investigation_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for error in string_items(report.get("errors")):
        out.append(
            finding(
                finding_type="ingest_error",
                title="Investigation input or step error",
                source=source,
                severity=SEVERITY_BASE["ingest_error"],
                confidence=0.92,
                evidence=[error],
                next_actions=["Fix the failing investigation input and rerun `python -m tools.debugger investigate`."],
            )
        )
    next_step = report.get("symptom_only_next_step")
    emitted_embedded_next_step = False
    if isinstance(next_step, dict):
        out.extend(next_step_findings(next_step, source=source))
        emitted_embedded_next_step = True
    for step in report.get("steps", []):
        if not isinstance(step, dict) or step.get("status") != "failed":
            continue
        out.append(
            finding(
                finding_type="workflow_failed",
                title=f"Investigation step failed: {step.get('id', '<unknown>')} {step.get('title', '')}".strip(),
                source=source,
                severity=SEVERITY_BASE["workflow_failed"],
                confidence=0.9,
                evidence=[
                    *string_items(step.get("errors")),
                    *string_items(step.get("warnings")),
                    f"report: {step.get('report_path', '')}",
                ],
                next_actions=string_items(step.get("commands"))[:4]
                or ["python -m tools.debugger investigate --report <failed-report.json>"],
            )
        )
    for item in report.get("top_findings", [])[:20]:
        if not isinstance(item, dict):
            continue
        if emitted_embedded_next_step and item.get("type") == "next_step":
            continue
        out.append(
            finding(
                finding_type=str(item.get("type", "ranked_finding")),
                title=str(item.get("title", "Investigation finding")),
                source=source,
                severity=int(item.get("severity", 40)),
                confidence=float(item.get("confidence", 0.6)),
                evidence=string_items(item.get("evidence"))[:4],
                next_actions=string_items(item.get("next_actions"))[:4],
            )
        )
    if report.get("passed") is False and not out:
        out.append(
            finding(
                finding_type="workflow_failed",
                title="Investigation did not pass",
                source=source,
                severity=SEVERITY_BASE["workflow_failed"],
                confidence=0.75,
                evidence=[f"failed_count={report.get('failed_count', 0)}"],
                next_actions=string_items(report.get("commands"))[:4]
                or ["python -m tools.debugger investigate --json --out-dir <dir>"],
            )
        )
    return out


def calibrate_finding_severity(item: dict[str, Any]) -> dict[str, Any]:
    match = first_rom_surface_match(finding_search_text(item))
    if not match:
        return item
    surface_id, surface, bonus = match
    base_severity = int(item.get("severity", 40))
    calibrated = dict(item)
    calibrated["severity_base"] = base_severity
    calibrated["severity_bonus"] = bonus
    calibrated["severity"] = min(95, base_severity + bonus)
    calibrated["surface_id"] = surface_id
    calibrated["surface"] = surface
    calibrated["evidence"] = unique_string_items(
        [
            *string_items(item.get("evidence")),
            f"ROM surface calibration: {surface} (+{bonus})",
        ]
    )
    return calibrated


def finding_search_text(item: dict[str, Any]) -> str:
    return " ".join(
        [
            str(item.get("type", "")),
            str(item.get("title", "")),
            " ".join(string_items(item.get("evidence"))),
            " ".join(string_items(item.get("next_actions"))),
        ]
    ).lower().replace("\\", "/")


def first_rom_surface_match(text: str) -> tuple[str, str, int] | None:
    for surface_id, surface, bonus, hints in ROM_SURFACE_SEVERITY_HINTS:
        if any(hint in text for hint in hints):
            return surface_id, surface, bonus
    return None


def finding(
    *,
    finding_type: str,
    title: str,
    source: str,
    severity: int,
    confidence: float,
    evidence: list[str],
    next_actions: list[str],
) -> dict[str, Any]:
    return {
        "type": finding_type,
        "title": title,
        "source": source,
        "severity": severity,
        "confidence": confidence,
        "evidence": [item for item in evidence if item],
        "next_actions": [item for item in next_actions if item],
    }


def string_items(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list | tuple | set):
        return [
            nested
            for item in value
            for nested in string_items(item)
        ]
    return [str(value)] if value else []


def dict_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list | tuple):
        return [item for item in value if isinstance(item, dict)]
    return []


def unique_string_items(values: list[str]) -> list[str]:
    out = []
    seen: set[str] = set()
    for value in values:
        text = str(value)
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def resolve_path(raw_path: str, *, root: Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return root / path


def display_path(path: Path, *, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path.resolve())


_FINDINGS_BUILDERS = {
    "unified_debugger_ingest_manifest": ingest_findings,
    "unified_debugger_capability_report": capability_findings,
    "unified_debugger_watch_report": watch_findings,
    "unified_debugger_runtime_state_report": runtime_state_findings,
    "unified_debugger_save_state_inspection": save_state_inspection_findings,
    "unified_debugger_replay_plan": replay_findings,
    "unified_debugger_setup_plan": setup_findings,
    "unified_debugger_gate_plan": gate_findings,
    "unified_debugger_compare_plan": compare_findings,
    "unified_debugger_content_mirror": content_mirror_findings,
    "unified_debugger_content_scenarios": content_scenario_findings,
    "unified_debugger_content_state_materialization": content_state_findings,
    "unified_debugger_state_space": state_space_findings,
    "unified_debugger_expectation_report": expectation_findings,
    "unified_debugger_test_suggestions": test_suggestion_findings,
    "unified_debugger_provenance_report": provenance_findings,
    "unified_debugger_causal_slice": slice_findings,
    "unified_debugger_taint_report": taint_findings,
    "unified_debugger_dynamic_taint_report": taint_findings,
    "unified_debugger_causal_explanation": explanation_findings,
    "unified_debugger_localization_plan": localization_findings,
    "unified_debugger_coverage_report": coverage_findings,
    "unified_debugger_trace_index": trace_index_findings,
    "unified_debugger_instruction_trace": instruction_trace_findings,
    "unified_debugger_next_step": next_step_findings,
    "unified_debugger_minimization_plan": minimization_findings,
    "unified_debugger_generation_plan": generation_findings,
    "unified_debugger_fuzz_plan": fuzz_findings,
    "unified_debugger_impact_report": impact_findings,
    "unified_debugger_visualization": visualization_findings,
    "unified_debugger_investigation_run": investigation_findings,
}
