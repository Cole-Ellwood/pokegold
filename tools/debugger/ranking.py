from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .address_boundary import (
    reverse_query_address_boundary_addresses,
    reverse_query_address_boundary_blocks_proof,
    reverse_query_address_boundary_evidence,
    reverse_query_address_boundary_fields,
)
from .catalog import ROOT
from .evidence import merge_evidence_atoms
from .workflow import command_address_arg


SEVERITY_BASE = {
    "gate_failed": 95,
    "ingest_error": 85,
    "workflow_failed": 82,
    "playtest_packet": 64,
    "watch_hit": 75,
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
    "expectation_failed": 78,
    "mirror_passed": 12,
    "mirror_uncovered": 50,
    "test_gap": 45,
    "coverage_gap": 40,
    "taint_path": 66,
    "reverse_attribution": 70,
    "reverse_query": 74,
    "effect_trace_observed": 72,
    "effect_trace_post_value_mismatch": 84,
    "effect_trace_unmodeled_change": 82,
    "effect_trace_unmodeled_effect": 80,
    "dynamic_taint_unmodeled_write": 78,
    "hardware_regression_blocker": 86,
    "cpu_state_side_effect": 80,
    "visual_snapshot": 52,
    "audio_snapshot": 52,
    "trace_synthesis_planned": 62,
    "instruction_trace_miss": 74,
    "instruction_trace_partial": 64,
    "instruction_trace_limit": 68,
    "instruction_trace_ready": 60,
    "provenance_warning": 30,
    "ingest_warning": 25,
}

PROOF_STATUSES = (
    "planned_only",
    "state_materialized",
    "runtime_observed",
    "instruction_observed",
    "taint_proven",
    "mirror_passed",
    "mirror_failed",
)

PROOF_STATUS_RANK = {
    "planned_only": 0,
    "state_materialized": 1,
    "mirror_passed": 2,
    "runtime_observed": 3,
    "instruction_observed": 4,
    "taint_proven": 5,
    "mirror_failed": 5,
}

PROOF_STATUS_SEVERITY_ADJUST = {
    "planned_only": -12,
    "state_materialized": -4,
    "mirror_passed": -2,
    "runtime_observed": 0,
    "instruction_observed": 3,
    "taint_proven": 5,
    "mirror_failed": 7,
}

PROOF_STATUS_IMPACT_SCORE = {
    "planned_only": -8,
    "state_materialized": -2,
    "mirror_passed": 1,
    "runtime_observed": 8,
    "instruction_observed": 10,
    "taint_proven": 12,
    "mirror_failed": 14,
}

ROM_SURFACE_SEVERITY_HINTS = (
    (
        "runtime_cpu_state",
        "Runtime execution and CPU state",
        9,
        (
            "cpu_state",
            "halted",
            "stopped",
            "softlock",
            "freeze",
            "frozen",
        ),
    ),
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
        "battle_mechanics_items_hazards",
        "Battle mechanics, items, and hazards",
        8,
        (
            "engine/battle/move_effects/spikes",
            "engine/battle/late_gen_held_items",
            "engine/battle/type_passive_damage_mods",
            "spikes",
            "rapid spin",
            "hazard",
            "hazards",
            "toxic",
            "burn",
            "paralysis",
            "reflect",
            "light screen",
            "safeguard",
            "substitute",
            "held item",
            "air balloon",
            "choice",
            "passive",
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
            "visual_snapshot",
            "audio_snapshot",
            "wtilemap",
            "wattrmap",
            "wshadowoam",
            "raud",
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
        "proof_status_counts": proof_status_counts(findings),
        "findings": findings,
    }


def findings_from_report(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    kind = report.get("kind", "")
    if kind == "unified_debugger_ingest_manifest":
        return ingest_findings(report, source=source)
    if kind == "unified_debugger_playtest_packet":
        return playtest_packet_findings(report, source=source)
    if kind == "unified_debugger_watch_report":
        return watch_findings(report, source=source)
    if kind == "unified_debugger_replay_plan":
        return replay_findings(report, source=source)
    if kind == "unified_debugger_setup_plan":
        return setup_findings(report, source=source)
    if kind == "unified_debugger_gate_plan":
        return gate_findings(report, source=source)
    if kind == "unified_debugger_compare_plan":
        return compare_findings(report, source=source)
    if kind == "unified_debugger_content_mirror":
        return content_mirror_findings(report, source=source)
    if kind == "unified_debugger_content_scenarios":
        return content_scenario_findings(report, source=source)
    if kind == "unified_debugger_content_state_materialization":
        return content_state_findings(report, source=source)
    if kind == "unified_debugger_state_space":
        return state_space_findings(report, source=source)
    if kind == "unified_debugger_expectation_report":
        return expectation_findings(report, source=source)
    if kind == "unified_debugger_test_suggestions":
        return test_suggestion_findings(report, source=source)
    if kind == "unified_debugger_provenance_report":
        return provenance_findings(report, source=source)
    if kind == "unified_debugger_causal_slice":
        return slice_findings(report, source=source)
    if kind in {"unified_debugger_taint_report", "unified_debugger_dynamic_taint_report"}:
        return taint_findings(report, source=source)
    if kind == "unified_debugger_causal_explanation":
        return explanation_findings(report, source=source)
    if kind == "unified_debugger_causal_graph":
        return causal_graph_findings(report, source=source)
    if kind == "unified_debugger_localization_plan":
        return localization_findings(report, source=source)
    if kind == "unified_debugger_coverage_report":
        return coverage_findings(report, source=source)
    if kind == "unified_debugger_trace_index":
        return trace_index_findings(report, source=source)
    if kind == "unified_debugger_instruction_trace":
        return instruction_trace_findings(report, source=source)
    if kind == "unified_debugger_effect_trace":
        return effect_trace_findings(report, source=source)
    if kind == "unified_debugger_reverse_query":
        return reverse_query_findings(report, source=source)
    if kind == "unified_debugger_hardware_regression_gate":
        return hardware_regression_findings(report, source=source)
    if kind == "unified_debugger_visual_snapshot":
        return visual_snapshot_findings(report, source=source)
    if kind == "unified_debugger_audio_snapshot":
        return audio_snapshot_findings(report, source=source)
    if kind == "unified_debugger_minimization_plan":
        return minimization_findings(report, source=source)
    if kind == "unified_debugger_generation_plan":
        return generation_findings(report, source=source)
    if kind == "unified_debugger_fuzz_plan":
        return fuzz_findings(report, source=source)
    if kind == "unified_debugger_impact_report":
        return impact_findings(report, source=source)
    if kind == "unified_debugger_visualization":
        return visualization_findings(report, source=source)
    if kind == "unified_debugger_investigation_run":
        return investigation_findings(report, source=source)
    if kind == "unified_debugger_impact_feedback":
        return []
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


def playtest_packet_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    reproducibility = report.get("reproducibility") if isinstance(report.get("reproducibility"), dict) else {}
    for error in string_items(report.get("errors"))[:8]:
        out.append(
            finding(
                finding_type="ingest_error",
                title="Playtest packet artifact error",
                source=source,
                severity=SEVERITY_BASE["ingest_error"],
                confidence=0.9,
                evidence=[error],
                next_actions=["Fix missing packet artifacts before replay/localization."],
            )
        )
    out.append(
        finding(
            finding_type="playtest_packet",
            title=f"Playtest packet: {report.get('symptom') or report.get('packet_id', source)}",
            source=source,
            severity=SEVERITY_BASE["playtest_packet"],
            confidence=0.78,
            evidence=[
                f"packet_id={report.get('packet_id', '')}",
                f"artifacts={report.get('artifact_count', 0)}",
                f"save_state={report.get('save_state', '')}",
                f"input_log={report.get('input_log', '')}",
                f"screenshot={report.get('screenshot', '')}",
                f"rom_sha256={str(report.get('rom_sha256', ''))[:12]}" if report.get("rom_sha256") else "",
                f"symbols_sha256={str(report.get('symbols_sha256', ''))[:12]}" if report.get("symbols_sha256") else "",
                f"runtime_replay_ready={reproducibility.get('runtime_replay_ready')}" if reproducibility else "",
                f"consistency={report.get('consistency_status_counts')}" if report.get("consistency_status_counts") else "",
                *string_items(report.get("warnings"))[:4],
                *string_items(report.get("notes"))[:4],
            ],
            next_actions=string_items(report.get("commands"))[:8],
            related_symbols=unique_string_items(
                [
                    *string_items(report.get("symbols_to_investigate")),
                    *string_items(report.get("watch_symbols")),
                ]
            ),
            related_files=string_items(report.get("changed_files")),
            related_addresses=string_items(report.get("addresses")),
            proof_status=str(report.get("proof_status") or "planned_only"),
        )
    )
    return out


def watch_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for event in report.get("events", []):
        address = event_related_address(event)
        out.append(
            finding(
                finding_type="watch_hit",
                title=f"{event.get('watch')} changed at {event.get('pc_bank_address')}",
                source=source,
                severity=SEVERITY_BASE["watch_hit"],
                confidence=0.8,
                evidence=[
                    f"{event.get('old_hex')} -> {event.get('new_hex')}",
                    f"address={address}" if address else "",
                    str(event.get("pc_label", "")),
                    f"context_frames={event.get('dynamic_context', {}).get('context_frame_count', 0)}",
                    watch_input_evidence(event),
                ],
                next_actions=string_items(event.get("commands"))[:4]
                or string_items(event.get("suggested_commands"))[:4],
                related_addresses=[address] if address else [],
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


def replay_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    watch_report = report.get("watch_report")
    if isinstance(watch_report, dict):
        out.extend(watch_findings(watch_report, source=source))
    confirmation = report.get("minimized_input_log_confirmation")
    if isinstance(confirmation, dict) and confirmation.get("attempted"):
        observed = confirmation.get("proof_status") == "runtime_observed"
        out.append(
            finding(
                finding_type="minimized_input_log_confirmation",
                title=(
                    "Minimized input log confirmed by runtime watch"
                    if observed
                    else "Minimized input log awaiting runtime confirmation"
                ),
                source=source,
                severity=64 if observed else 50,
                confidence=0.82 if observed else 0.62,
                evidence=string_items(confirmation.get("evidence"))[:8],
                next_actions=string_items(confirmation.get("commands"))[:8]
                or replay_report_commands(report)[:8],
                related_symbols=string_items(confirmation.get("watch_symbols")),
                related_addresses=string_items(confirmation.get("watch_addresses")),
                proof_status=str(confirmation.get("proof_status") or "planned_only"),
            )
        )
    state_patch_confirmation = report.get("minimized_state_patch_confirmation")
    if isinstance(state_patch_confirmation, dict) and state_patch_confirmation.get("attempted"):
        observed = state_patch_confirmation.get("proof_status") == "runtime_observed"
        out.append(
            finding(
                finding_type="minimized_state_patch_confirmation",
                title=(
                    "Minimized state patch confirmed by runtime watch"
                    if observed
                    else "Minimized state patch awaiting runtime confirmation"
                ),
                source=source,
                severity=65 if observed else 51,
                confidence=0.82 if observed else 0.62,
                evidence=string_items(state_patch_confirmation.get("evidence"))[:8],
                next_actions=string_items(state_patch_confirmation.get("commands"))[:8]
                or replay_report_commands(report)[:8],
                related_symbols=string_items(state_patch_confirmation.get("watch_symbols")),
                related_addresses=string_items(state_patch_confirmation.get("watch_addresses")),
                proof_status=str(state_patch_confirmation.get("proof_status") or "planned_only"),
            )
        )
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


def replay_report_commands(report: dict[str, Any]) -> list[str]:
    commands: list[str] = []
    for command in string_items(report.get("commands")):
        commands.append(command)
    for phase in dict_items(report.get("phase_steps")):
        for step in dict_items(phase.get("steps")):
            commands.extend(string_items(step.get("command")))
    return unique_string_items(commands)


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
        if match.get("status") == "passed":
            out.append(
                finding(
                    finding_type="mirror_passed",
                    title=f"Mirror passed: {match.get('id')}",
                    source=source,
                    severity=SEVERITY_BASE["mirror_passed"],
                    confidence=0.82,
                    evidence=string_items(match.get("evidence"))[:8],
                    next_actions=list(match.get("commands", []))[:4],
                    related_symbols=string_items(match.get("related_symbols")),
                    related_addresses=string_items(match.get("related_addresses")),
                    related_files=string_items(match.get("source_files")),
                    proof_status=str(match.get("proof_status") or "mirror_passed"),
                )
            )
        for gap in match.get("gaps", []):
            out.append(
                finding(
                    finding_type="compare_gap",
                    title=f"Mirror gap: {match.get('id')}",
                    source=source,
                    severity=SEVERITY_BASE["compare_gap"],
                    confidence=0.65,
                    evidence=[gap, *string_items(match.get("evidence"))[:4]],
                    next_actions=list(match.get("materialization_commands", []))[:4],
                    related_symbols=string_items(match.get("related_symbols")),
                    related_addresses=string_items(match.get("related_addresses")),
                    related_files=string_items(match.get("source_files")),
                    proof_status=str(match.get("proof_status") or ""),
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
                related_symbols=string_items(item.get("related_symbols")),
                related_files=string_items(item.get("related_files")) or string_items(item.get("source_file")),
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
                evidence=content_scenario_evidence(scenario),
                next_actions=content_scenario_commands(scenario)[:6],
                related_symbols=content_scenario_related_symbols(scenario),
                related_files=content_scenario_related_files(scenario),
            )
        )
    return out


def content_scenario_commands(scenario: dict[str, Any]) -> list[str]:
    materialization_request = scenario.get("materialization_request")
    commands: list[str] = []
    if isinstance(materialization_request, dict):
        commands.extend(string_items(materialization_request.get("commands")))
    probe_commands: list[str] = []
    for probe in scenario.get("behavioral_probes", []):
        if isinstance(probe, dict):
            probe_commands.extend(string_items(probe.get("command")))
    commands.extend(probe_commands)
    commands.extend(string_items(scenario.get("commands")))
    return unique_string_items(commands)


def content_scenario_evidence(scenario: dict[str, Any]) -> list[str]:
    source_file = str(scenario.get("source_file", ""))
    runtime_targets = scenario.get("runtime_targets") if isinstance(scenario.get("runtime_targets"), dict) else {}
    out = [
        f"{source_file}:{scenario.get('line', 0)}" if source_file else "",
        f"scenario_type={scenario.get('scenario_type')}" if scenario.get("scenario_type") else "",
        f"proof_level={scenario.get('proof_level')}" if scenario.get("proof_level") else "",
        f"runtime_route={runtime_targets.get('runtime_route')}" if runtime_targets.get("runtime_route") else "",
    ]
    for precondition in dict_items(scenario.get("state_preconditions")):
        kind = str(precondition.get("kind", ""))
        if kind:
            out.append(f"precondition={kind}")
        out.extend(f"watch_symbol={symbol}" for symbol in string_items(precondition.get("watch_symbols")))
    for probe in dict_items(scenario.get("behavioral_probes")):
        probe_id = str(probe.get("id", ""))
        if probe_id:
            out.append(f"behavioral_probe={probe_id}")
    for key in ("source_symbols", "script_symbols", "trace_symbols", "watch_symbols"):
        role = key[:-1] if key.endswith("s") else key
        out.extend(f"{role}={symbol}" for symbol in string_items(runtime_targets.get(key)))
    out.extend(string_items(scenario.get("expected"))[:6])
    return unique_string_items([item for item in out if item])


def content_scenario_related_symbols(scenario: dict[str, Any]) -> list[str]:
    runtime_targets = scenario.get("runtime_targets") if isinstance(scenario.get("runtime_targets"), dict) else {}
    symbols = [
        *string_items(scenario.get("related_symbols")),
        *string_items(scenario.get("symbols")),
    ]
    for key in ("source_symbols", "script_symbols", "trace_symbols", "watch_symbols"):
        symbols.extend(string_items(runtime_targets.get(key)))
    for precondition in dict_items(scenario.get("state_preconditions")):
        symbols.extend(string_items(precondition.get("watch_symbols")))
    return unique_string_items([symbol for symbol in symbols if symbol])


def content_scenario_related_files(scenario: dict[str, Any]) -> list[str]:
    runtime_targets = scenario.get("runtime_targets") if isinstance(scenario.get("runtime_targets"), dict) else {}
    files = [
        str(scenario.get("source_file", "")),
        *string_items(scenario.get("related_files")),
        *string_items(runtime_targets.get("source_files")),
    ]
    for probe in dict_items(scenario.get("behavioral_probes")):
        files.extend(string_items(probe.get("source_file")))
    return unique_string_items([normalize_path(path) for path in files if path])


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
                    *save_state_delta_evidence(materialized_save_state_delta(report)),
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


def materialized_save_state_delta(report: dict[str, Any]) -> dict[str, Any]:
    execution = report.get("execution") if isinstance(report.get("execution"), dict) else {}
    state_space = report.get("state_space") if isinstance(report.get("state_space"), dict) else {}
    for candidate in (
        execution.get("save_state_delta"),
        report.get("save_state_delta"),
        state_space.get("save_state_delta"),
    ):
        if save_state_delta_has_evidence(candidate):
            return candidate
    return {}


def save_state_delta_has_evidence(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    return any(
        key in value
        for key in (
            "attempted",
            "proof_status",
            "changed_byte_count",
            "changed_offsets",
            "errors",
        )
    )


def save_state_delta_has_delta_detail(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    return any(key in value for key in ("changed_byte_count", "changed_offsets", "errors"))


def minimized_state_patch_save_state_delta(item: dict[str, Any]) -> dict[str, Any]:
    summarized = item.get("minimized_save_state_delta")
    if save_state_delta_has_delta_detail(summarized):
        return summarized
    data = item.get("data") if isinstance(item.get("data"), dict) else {}
    materialized = materialized_save_state_delta(data)
    if save_state_delta_has_delta_detail(materialized):
        return materialized
    if save_state_delta_has_evidence(summarized):
        return summarized
    return {}


def save_state_delta_evidence(delta: Any, *, prefix: str = "save_state_delta") -> list[str]:
    if not isinstance(delta, dict):
        return []
    out = []
    if "changed_byte_count" in delta:
        out.append(f"{prefix}_changed_bytes={delta.get('changed_byte_count', 0)}")
    offsets = delta.get("changed_offsets")
    if isinstance(offsets, list | tuple):
        offset_text = ",".join(str(offset) for offset in offsets[:8])
        if offset_text:
            out.append(f"{prefix}_offsets={offset_text}")
        if delta.get("changed_offsets_truncated"):
            out.append(f"{prefix}_offsets_truncated=true")
    proof_status = str(delta.get("proof_status") or "")
    if proof_status:
        out.append(f"{prefix}_proof_status={proof_status}")
    for error in string_items(delta.get("errors"))[:3]:
        out.append(f"{prefix}_error={error}")
    return out


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
                    *save_state_delta_evidence(materialized_save_state_delta(report)),
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
    for route in trace_synthesis_routes(report)[:20]:
        out.append(
            finding(
                finding_type="trace_synthesis_planned",
                title=trace_synthesis_title(route),
                source=source,
                severity=trace_synthesis_severity(route),
                confidence=0.78,
                evidence=trace_synthesis_evidence(route),
                next_actions=string_items(route.get("commands"))[:8] or string_items(report.get("commands"))[:8],
                related_symbols=trace_synthesis_related_symbols(route),
                related_addresses=trace_synthesis_related_addresses(route),
            )
        )
    for diagnostic in dynamic_taint_unmodeled_write_diagnostics(report)[:20]:
        out.append(
            finding(
                finding_type="dynamic_taint_unmodeled_write",
                title=f"Dynamic taint observed unmodeled write: {diagnostic.get('pc_label', '<pc>')}",
                source=source,
                severity=SEVERITY_BASE["dynamic_taint_unmodeled_write"],
                confidence=0.72,
                evidence=dynamic_taint_unmodeled_write_evidence(diagnostic),
                next_actions=string_items(diagnostic.get("commands"))[:6] or string_items(report.get("commands"))[:6],
                related_symbols=string_items(diagnostic.get("related_symbols")),
                related_addresses=string_items(diagnostic.get("related_addresses")),
                proof_status=str(diagnostic.get("proof_status") or "instruction_observed"),
                evidence_atoms=diagnostic.get("evidence_atoms"),
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
                related_symbols=string_items(path.get("related_symbols")),
                related_files=string_items(path.get("related_files")),
                related_addresses=string_items(path.get("related_addresses")),
                proof_status=str(path.get("proof_status") or ""),
                evidence_atoms=path.get("evidence_atoms"),
            )
        )
    for attribution in report.get("write_attributions", [])[:20]:
        if not isinstance(attribution, dict):
            continue
        addresses = attribution_related_addresses(attribution)
        out.append(
            finding(
                finding_type="reverse_attribution",
                title=f"Dynamic write: {attribution.get('target', '<sink>')} at {attribution.get('pc_label', '<pc>')}",
                source=source,
                severity=min(92, max(SEVERITY_BASE["reverse_attribution"], int(attribution.get("score", 0)))),
                confidence=float(attribution.get("confidence", 0.72)),
                evidence=[
                    *list(attribution.get("evidence", []))[:5],
                    *attribution_proof_evidence(attribution),
                    *[f"address={address}" for address in addresses],
                ],
                next_actions=list(attribution.get("commands", []))[:5],
                related_symbols=string_items(attribution.get("related_symbols")),
                related_files=string_items(attribution.get("related_files")),
                related_addresses=addresses,
                proof_status=str(attribution.get("proof_status") or ""),
                evidence_atoms=attribution.get("evidence_atoms"),
            )
        )
    return out


def dynamic_taint_unmodeled_write_diagnostics(report: dict[str, Any]) -> list[dict[str, Any]]:
    diagnostics = dict_items(report.get("unmodeled_write_diagnostics"))
    if diagnostics:
        return diagnostics
    return [
        diagnostic
        for run in dict_items(report.get("trace_runs"))
        for diagnostic in dict_items(run.get("unmodeled_write_diagnostics"))
    ]


def dynamic_taint_unmodeled_write_evidence(diagnostic: dict[str, Any]) -> list[str]:
    evidence = string_items(diagnostic.get("evidence"))
    if evidence:
        return evidence[:8]
    return [
        f"seq={diagnostic.get('seq')}",
        f"pc={diagnostic.get('pc_bank_address', '')}",
        f"operation={diagnostic.get('operation', '')}",
        "missing=" + ",".join(string_items(diagnostic.get("missing_registers"))),
        f"address_source={diagnostic.get('address_source', '')}",
        f"target_match_proof_status={diagnostic.get('target_match_proof_status', '')}",
        f"attribution_status={diagnostic.get('attribution_status', '')}",
    ]


def trace_synthesis_routes(report: dict[str, Any]) -> list[dict[str, Any]]:
    plan = report.get("trace_synthesis_plan") if isinstance(report.get("trace_synthesis_plan"), dict) else {}
    return dict_items(plan.get("routes"))


def trace_synthesis_title(route: dict[str, Any]) -> str:
    match_id = str(route.get("match_id") or route.get("source_kind") or route.get("id") or "route")
    return f"Dynamic-taint trace synthesis planned: {match_id}"


def trace_synthesis_severity(route: dict[str, Any]) -> int:
    status = str(route.get("state_status", ""))
    base = SEVERITY_BASE["trace_synthesis_planned"]
    return base + 4 if status.startswith("requires") else base


def trace_synthesis_evidence(route: dict[str, Any]) -> list[str]:
    return [
        f"source_kind={route.get('source_kind', '')}",
        f"match_id={route.get('match_id', '')}",
        f"state_status={route.get('state_status', '')}",
        f"scenario_ids={','.join(string_items(route.get('scenario_ids'))[:6])}",
        f"source_symbols={','.join(string_items(route.get('source_symbols'))[:8])}",
        f"source_mems={','.join(string_items(route.get('source_mems'))[:8])}",
        f"sink_symbols={','.join(string_items(route.get('sink_symbols'))[:8])}",
        f"sink_addresses={','.join(string_items(route.get('sink_addresses'))[:8])}",
        f"save_state={route.get('save_state', '')}",
        f"trace_output={route.get('trace_output', '')}",
    ]


def trace_synthesis_related_symbols(route: dict[str, Any]) -> list[str]:
    return unique_string_items(
        [
            *string_items(route.get("sink_symbols")),
            *string_items(route.get("source_symbols")),
            *source_mem_origins(route),
        ]
    )


def trace_synthesis_related_addresses(route: dict[str, Any]) -> list[str]:
    return unique_string_items(
        [
            *string_items(route.get("sink_addresses")),
            *source_mem_addresses(route),
        ]
    )


def source_mem_origins(route: dict[str, Any]) -> list[str]:
    return unique_string_items(
        [
            origin
            for _, origin in source_mem_parts(route)
            if origin
        ]
    )


def source_mem_addresses(route: dict[str, Any]) -> list[str]:
    return unique_string_items(
        [
            address
            for address, _ in source_mem_parts(route)
            if address
        ]
    )


def source_mem_parts(route: dict[str, Any]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for value in string_items(route.get("source_mems")):
        text = str(value).strip()
        if not text:
            continue
        if "=" in text:
            address, origin = text.split("=", 1)
            out.append((address.strip(), origin.strip()))
        else:
            out.append((text, ""))
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
                related_symbols=instruction_trace_related_symbols(report, validation),
                related_addresses=instruction_trace_related_addresses(report, validation),
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
                related_symbols=instruction_trace_related_symbols(report, validation),
                related_addresses=instruction_trace_related_addresses(report, validation),
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
                related_symbols=instruction_trace_related_symbols(report, validation),
                related_addresses=instruction_trace_related_addresses(report, validation),
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
                evidence=[
                    *instruction_trace_validation_evidence(report, validation),
                    played_input_summary_evidence(report),
                ],
                next_actions=instruction_trace_dynamic_taint_commands(report, validation, trace_path=trace_path),
                related_symbols=instruction_trace_related_symbols(report, validation),
                related_addresses=instruction_trace_related_addresses(report, validation),
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


def watch_input_evidence(event: dict[str, Any]) -> str:
    input_context = event.get("input_context") if isinstance(event.get("input_context"), dict) else {}
    last_input = input_context.get("last_input") if isinstance(input_context.get("last_input"), dict) else {}
    buttons = "+".join(string_items(last_input.get("buttons"))) if last_input else ""
    if not buttons:
        return ""
    return f"last_input={buttons}@frame{last_input.get('frame', '')}"


def played_input_summary_evidence(report: dict[str, Any]) -> str:
    count = int(report.get("played_input_count", 0) or 0)
    if not count:
        return ""
    return f"played_inputs={count}"


def effect_trace_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for error in string_items(report.get("errors"))[:8]:
        out.append(
            finding(
                finding_type="ingest_error",
                title="Effect trace input error",
                source=source,
                severity=SEVERITY_BASE["ingest_error"],
                confidence=0.88,
                evidence=[error],
                next_actions=["python -m tools.debugger trace-instructions --execute --out-trace <trace.jsonl>"],
            )
        )
    watch_write_count = int(report.get("watch_write_count", 0) or 0)
    write_index = dict_items(report.get("write_index"))
    side_effect_index = dict_items(report.get("side_effect_index"))
    unmodeled_effect_count = int(report.get("unmodeled_effect_count", 0) or 0)
    register_write_count = int(report.get("register_write_count", 0) or 0)
    if watch_write_count or write_index or side_effect_index or unmodeled_effect_count or register_write_count:
        top = sorted(write_index, key=effect_index_priority)[:8]
        side_effect_top = sorted(
            side_effect_index,
            key=side_effect_priority,
        )[:6]
        watch_hit_summaries = effect_trace_watch_hit_summaries(report)
        watch_hits = [
            hit
            for event in dict_items(report.get("events"))
            for hit in dict_items(event.get("watch_hits"))
        ]
        bank_unverified_hits = sum(
            1
            for hit in watch_hits
            if str(hit.get("bank_match", "")) == "bus_address_unverified_bank"
        )
        bank_unverified_write_hits = sum(
            1
            for hit in watch_hits
            if hit.get("access") == "write" and str(hit.get("bank_match", "")) == "bus_address_unverified_bank"
        )
        verified_watch_write_hits = sum(
            1
            for hit in watch_hits
            if hit.get("access") == "write" and str(hit.get("bank_match", "")) != "bus_address_unverified_bank"
        )
        target_match_proof_status = effect_trace_target_match_proof_status(
            bank_unverified_write_hits=bank_unverified_write_hits,
            verified_watch_write_hits=verified_watch_write_hits,
        )
        post_value_matches = int(report.get("post_value_match_count", 0) or 0)
        post_value_mismatches = int(report.get("post_value_mismatch_count", 0) or 0)
        post_register_matches = int(report.get("post_register_match_count", 0) or 0)
        post_register_mismatches = int(report.get("post_register_mismatch_count", 0) or 0)
        unmodeled_changes = int(report.get("unmodeled_observed_change_count", 0) or 0)
        mismatch_summaries = effect_trace_post_value_mismatch_summaries(report)
        if mismatch_summaries:
            out.append(
                finding(
                    finding_type="effect_trace_post_value_mismatch",
                    title="Effect trace modeled write disagrees with next captured frame",
                    source=source,
                    severity=SEVERITY_BASE["effect_trace_post_value_mismatch"] + min(6, len(mismatch_summaries)),
                    confidence=0.78,
                    evidence=[
                        "next-frame observed byte did not match modeled write value",
                        *mismatch_summaries[:8],
                    ],
                    next_actions=string_items(report.get("commands"))[:6]
                    or ["python -m tools.debugger hook-order-probe --execute"],
                    related_addresses=effect_trace_post_value_mismatch_addresses(report),
                    proof_status="instruction_observed",
                )
            )
        unmodeled_summaries = effect_trace_unmodeled_change_summaries(report)
        if unmodeled_summaries:
            out.append(
                finding(
                    finding_type="effect_trace_unmodeled_change",
                    title="Effect trace observed byte changes without a modeled writer",
                    source=source,
                    severity=SEVERITY_BASE["effect_trace_unmodeled_change"] + min(6, len(unmodeled_summaries)),
                    confidence=0.74,
                    evidence=[
                        "adjacent captured frames changed observed memory without a modeled write effect",
                        *unmodeled_summaries[:8],
                    ],
                    next_actions=string_items(report.get("commands"))[:6]
                    or ["python -m tools.debugger effect-trace --trace <trace.jsonl>"],
                    related_addresses=effect_trace_unmodeled_change_addresses(report),
                    proof_status="instruction_observed",
                )
            )
        unmodeled_effect_summaries = effect_trace_unmodeled_effect_summaries(report)
        if unmodeled_effect_summaries:
            out.append(
                finding(
                    finding_type="effect_trace_unmodeled_effect",
                    title="Effect trace observed instructions with unmodeled effects",
                    source=source,
                    severity=SEVERITY_BASE["effect_trace_unmodeled_effect"] + min(6, len(unmodeled_effect_summaries)),
                    confidence=0.72,
                    evidence=[
                        "instruction frames were observed but required pre-instruction registers were missing",
                        *unmodeled_effect_summaries[:8],
                    ],
                    next_actions=string_items(report.get("commands"))[:6]
                    or ["python -m tools.debugger trace-instructions --symbol <routine> --watch-address <address> --execute"],
                    related_addresses=[],
                    proof_status="instruction_observed",
                )
            )
        out.extend(cpu_state_side_effect_findings(
            side_effect_index=side_effect_index,
            source=source,
            commands=string_items(report.get("commands")),
        ))
        out.append(
            finding(
                finding_type="effect_trace_observed",
                title=f"Effect trace observed {watch_write_count} watched writes",
                source=source,
                severity=SEVERITY_BASE["effect_trace_observed"] + min(8, watch_write_count),
                confidence=effect_trace_confidence(watch_write_count=watch_write_count, bank_unverified_hits=bank_unverified_hits),
                evidence=[
                    f"effect_events={report.get('effect_event_count', 0)}",
                    f"bank_unverified_watch_hits={bank_unverified_hits}" if bank_unverified_hits else "",
                    "effect_proof_status=instruction_observed" if bank_unverified_hits else "",
                    (
                        f"target_match_proof_status={target_match_proof_status}"
                        if bank_unverified_hits
                        else ""
                    ),
                    (
                        "proof_downgrade_reason=bank-qualified watch matched effect by bus address "
                        "without runtime bank state"
                        if bank_unverified_hits
                        else ""
                    ),
                    f"memory_writes={report.get('memory_write_count', 0)}",
                    f"stack_writes={report.get('stack_write_count', 0)}",
                    f"io_writes={report.get('io_write_count', 0)}",
                    f"register_writes={register_write_count}",
                    f"hardware_side_effects={report.get('hardware_side_effect_count', 0)}",
                    f"dma_copy_writes={report.get('dma_copy_write_count', 0)}",
                    f"interrupt_entries={report.get('interrupt_entry_count', 0)}",
                    f"unmodeled_effects={unmodeled_effect_count}" if unmodeled_effect_count else "",
                    f"post_value_matches={post_value_matches}" if post_value_matches else "",
                    f"post_value_mismatches={post_value_mismatches}" if post_value_mismatches else "",
                    f"post_register_matches={post_register_matches}" if post_register_matches else "",
                    f"post_register_mismatches={post_register_mismatches}" if post_register_mismatches else "",
                    f"unmodeled_observed_changes={unmodeled_changes}" if unmodeled_changes else "",
                    f"hook_order_proof={report.get('hook_order_proof_status', '')}"
                    if report.get("hook_order_validation_count")
                    else "",
                    f"hook_order_proof_boundary={report.get('hook_order_proof_boundary', '')}"
                    if report.get("hook_order_proof_boundary")
                    else "",
                    (
                        "hook_order_non_mutating_instruction_events="
                        f"{report.get('hook_order_non_mutating_instruction_events')}"
                    )
                    if report.get("hook_order_non_mutating_instruction_events") not in {None, ""}
                    else "",
                    *watch_hit_summaries[:8],
                    *[
                        f"{item.get('address', '')}: writes={item.get('write_count', 0)} last={item.get('last_writer_pc', '')}"
                        for item in top
                    ],
                    *[
                        side_effect_summary(item)
                        for item in side_effect_top
                    ],
                ],
                next_actions=string_items(report.get("commands"))[:6]
                or ["python -m tools.debugger dynamic-taint --trace <trace.jsonl> --sink-address <address>"],
                related_addresses=[
                    str(item.get("address", ""))
                    for item in top
                    if item.get("address")
                ],
                proof_status=target_match_proof_status,
            )
        )
    return out


def effect_trace_confidence(*, watch_write_count: int, bank_unverified_hits: int) -> float:
    confidence = 0.84 if watch_write_count else 0.7
    if bank_unverified_hits:
        return min(confidence, 0.72)
    return confidence


def effect_trace_target_match_proof_status(
    *,
    bank_unverified_write_hits: int,
    verified_watch_write_hits: int,
) -> str:
    if bank_unverified_write_hits and not verified_watch_write_hits:
        return "planned_only"
    return "instruction_observed"


def effect_trace_post_value_mismatch_summaries(report: dict[str, Any]) -> list[str]:
    summaries: list[str] = []
    for event in dict_items(report.get("events")):
        pc = str(event.get("pc_bank_address", ""))
        seq = event.get("seq")
        for item in dict_items(event.get("effects")):
            if item.get("post_value_status") != "mismatch":
                continue
            summaries.append(
                " ".join(
                    part
                    for part in [
                        f"seq={seq}",
                        f"pc={pc}",
                        f"address={item.get('address_hex', '')}",
                        f"operation={item.get('operation', '')}",
                        f"modeled={item.get('value_hex', '')}",
                        f"observed={item.get('post_value_hex', '')}",
                        f"next_pc={item.get('post_observed_pc', '')}",
                    ]
                    if part and not part.endswith("=")
                )
            )
    return unique_string_items(summaries)


def effect_trace_post_value_mismatch_addresses(report: dict[str, Any]) -> list[str]:
    return unique_string_items(
        str(item.get("address_hex", ""))
        for event in dict_items(report.get("events"))
        for item in dict_items(event.get("effects"))
        if item.get("post_value_status") == "mismatch" and item.get("address_hex")
    )


def effect_trace_unmodeled_change_summaries(report: dict[str, Any]) -> list[str]:
    summaries: list[str] = []
    for event in dict_items(report.get("events")):
        for change in dict_items(event.get("unmodeled_observed_changes")):
            summaries.append(
                " ".join(
                    part
                    for part in [
                        f"seq={change.get('seq', event.get('seq'))}",
                        f"pc={change.get('pc', event.get('pc_bank_address', ''))}",
                        f"address={change.get('address', '')}",
                        f"old={change.get('old_value_hex', '')}",
                        f"new={change.get('new_value_hex', '')}",
                        f"next_pc={change.get('next_pc', '')}",
                    ]
                    if part and not part.endswith("=")
                )
            )
    return unique_string_items(summaries)


def effect_trace_unmodeled_change_addresses(report: dict[str, Any]) -> list[str]:
    return unique_string_items(
        str(change.get("address", ""))
        for event in dict_items(report.get("events"))
        for change in dict_items(event.get("unmodeled_observed_changes"))
        if change.get("address")
    )


def effect_trace_unmodeled_effect_summaries(report: dict[str, Any]) -> list[str]:
    summaries: list[str] = []
    for event in dict_items(report.get("events")):
        for item in dict_items(event.get("effects")):
            if item.get("access") != "unmodeled":
                continue
            summaries.append(
                " ".join(
                    part
                    for part in [
                        f"seq={event.get('seq')}",
                        f"pc={event.get('pc_bank_address', '')}",
                        f"operation={item.get('operation', '')}",
                        f"reason={item.get('evidence_status', '')}",
                        "missing=" + ",".join(string_items(item.get("missing_registers"))),
                    ]
                    if part and not part.endswith("=")
                )
            )
    return unique_string_items(summaries)


def effect_trace_watch_hit_summaries(report: dict[str, Any]) -> list[str]:
    summaries: list[str] = []
    for event in dict_items(report.get("events")):
        pc = str(event.get("pc_bank_address", ""))
        for hit in dict_items(event.get("watch_hits")):
            summaries.append(
                " ".join(
                    part
                    for part in [
                        "watch_hit",
                        str(hit.get("watch", "")),
                        f"access={hit.get('access', '')}",
                        f"address={hit.get('address', '')}",
                        f"value={hit.get('value_hex', '')}" if hit.get("value_hex") else "",
                        f"pc={pc}" if pc else "",
                        f"match_precision={hit.get('match_precision', '')}" if hit.get("match_precision") else "",
                        f"bank_match={hit.get('bank_match', '')}" if hit.get("bank_match") else "",
                        f"bank_source={hit.get('bank_source', '')}" if hit.get("bank_source") else "",
                        (
                            f"target_match_proof_status={hit.get('target_match_proof_status', '')}"
                            if hit.get("target_match_proof_status")
                            else ""
                        ),
                        (
                            f"proof_downgrade_reason={hit.get('proof_downgrade_reason', '')}"
                            if hit.get("proof_downgrade_reason")
                            else ""
                        ),
                    ]
                    if part
                )
            )
    return unique_string_items(summaries)


def cpu_state_side_effect_findings(
    *,
    side_effect_index: list[dict[str, Any]],
    source: str,
    commands: list[str],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in side_effect_index:
        if str(item.get("kind", "")) != "cpu_state" and str(item.get("category", "")) != "cpu":
            continue
        operations = side_effect_trigger_values(item, "operation")
        modes = side_effect_trigger_values(item, "mode")
        pcs = side_effect_trigger_values(item, "pc")
        title_ops = "/".join(operation.upper() for operation in operations) or "CPU state"
        out.append(
            finding(
                finding_type="cpu_state_side_effect",
                title=f"CPU liveness transition observed: {title_ops}",
                source=source,
                severity=SEVERITY_BASE["cpu_state_side_effect"],
                confidence=0.87,
                evidence=[
                    side_effect_summary(item),
                    f"operations={','.join(operations)}" if operations else "",
                    f"modes={','.join(modes)}" if modes else "",
                    f"pcs={','.join(pcs[:6])}" if pcs else "",
                    "cpu_state can indicate a freeze, softlock, or interrupt-waiting path when it appears in the symptom window",
                ],
                next_actions=commands[:6]
                or [
                    "python -m tools.debugger visualize --report <effect-trace.json>",
                    "python -m tools.debugger causal-graph --report <effect-trace.json>",
                ],
                semantic_factors=["cpu_liveness_state: CPU halted/stopped liveness transition (+14)"],
                proof_status="instruction_observed",
            )
        )
    return out


def side_effect_priority(item: dict[str, Any]) -> tuple[int, int, str]:
    kind = str(item.get("kind", ""))
    category = str(item.get("category", ""))
    priority = {
        "cpu_state": 0,
        "interrupt_entry": 1,
        "ime": 2,
        "oam_dma_trigger": 3,
    }.get(kind, 4)
    if category == "cpu":
        priority = min(priority, 0)
    elif category == "interrupt":
        priority = min(priority, 1)
    return (priority, -int(item.get("count", 0) or 0), kind)


def side_effect_summary(item: dict[str, Any]) -> str:
    parts = [
        f"side_effect {item.get('kind', '')}: count={item.get('count', 0)} last={item.get('last_pc', '')}",
    ]
    operations = side_effect_trigger_values(item, "operation")
    modes = side_effect_trigger_values(item, "mode")
    transfer_models = side_effect_trigger_values(item, "transfer_model")
    transfer_blocked_reasons = side_effect_trigger_values(item, "transfer_blocked_reason")
    source_ranges = side_effect_trigger_values(item, "source_range")
    target_ranges = side_effect_trigger_values(item, "target_range")
    if operations:
        parts.append("operations=" + ",".join(operations[:6]))
    if modes:
        parts.append("modes=" + ",".join(modes[:6]))
    if transfer_models:
        parts.append("transfer_models=" + ",".join(transfer_models[:4]))
    if transfer_blocked_reasons:
        parts.append("transfer_blocked_reasons=" + ",".join(transfer_blocked_reasons[:4]))
    if source_ranges:
        parts.append("source_ranges=" + ",".join(source_ranges[:4]))
    if target_ranges:
        parts.append("target_ranges=" + ",".join(target_ranges[:4]))
    return " ".join(parts)


def side_effect_trigger_values(item: dict[str, Any], key: str) -> list[str]:
    return unique_string_items(
        str(trigger.get(key, ""))
        for trigger in dict_items(item.get("triggers"))
        if trigger.get(key)
    )


def effect_index_priority(item: dict[str, Any]) -> tuple[int, int, str]:
    history = dict_items(item.get("history"))
    has_hardware_modeled_write = any(
        str(entry.get("access", "")) == "write" and str(entry.get("kind", "")).startswith("dma_")
        for entry in history
    )
    modeled_penalty = 1 if has_hardware_modeled_write else 0
    return (
        modeled_penalty,
        -int(item.get("write_count", 0) or 0),
        str(item.get("address", "")),
    )


def reverse_query_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for error in string_items(report.get("errors"))[:8]:
        out.append(
            finding(
                finding_type="ingest_error",
                title="Reverse query input error",
                source=source,
                severity=SEVERITY_BASE["ingest_error"],
                confidence=0.86,
                evidence=[error],
                next_actions=["python -m tools.debugger reverse-query --report <effect-trace.json> --address <address>"],
            )
        )
    for result in dict_items(report.get("results"))[:20]:
        target = result.get("target") if isinstance(result.get("target"), dict) else {}
        label = str(target.get("label") or target.get("symbol") or result.get("matched_address") or "target")
        last_writer = result.get("last_writer") if isinstance(result.get("last_writer"), dict) else {}
        result_evidence = string_items(result.get("evidence"))
        address_boundary_evidence = reverse_query_address_boundary_evidence(result)
        value_source_evidence = [
            item
            for item in result_evidence
            if item.startswith("value_source=")
        ]
        observed_memory_evidence = [
            item
            for item in result_evidence
            if item.startswith("observed_memory=")
        ]
        register_evidence = [
            item
            for item in result_evidence
            if item.startswith(("pre_A=", "pre_F=", "pre_HL=", "pre_SP="))
        ]
        pre_state_evidence = [
            item
            for item in result_evidence
            if item.startswith("pre_state_")
        ]
        proof_status = str(result.get("proof_status") or report.get("proof_status") or "planned_only")
        if reverse_query_address_boundary_blocks_proof(result):
            proof_status = "planned_only"
        finding_item = finding(
            finding_type="reverse_query",
            title=f"Reverse query: {label} last written at {result.get('last_writer_pc', '')}",
            source=source,
            severity=SEVERITY_BASE["reverse_query"] + min(8, int(result.get("write_count", 0) or 0)),
            confidence=0.88 if last_writer else 0.68,
            evidence=[
                *address_boundary_evidence,
                *result_evidence[:6],
                *value_source_evidence[:2],
                *observed_memory_evidence[:4],
                *register_evidence[:4],
                *pre_state_evidence[:4],
                f"validation={result.get('validation', {}).get('status', '')}" if isinstance(result.get("validation"), dict) else "",
                f"history={len(dict_items(result.get('history')))}",
            ],
            next_actions=reverse_query_next_actions(result, report),
            related_symbols=string_items(target.get("symbol")),
            related_addresses=unique_string_items(
                [
                    *reverse_query_address_boundary_addresses(result),
                    str(target.get("evidence") or ""),
                    str(result.get("matched_address") or ""),
                    *[
                        str(item.get("address", ""))
                        for item in dict_items(result.get("history"))
                        if item.get("address")
                    ],
                ]
            ),
            proof_status=proof_status,
        )
        finding_item.update(reverse_query_address_boundary_fields(result))
        out.append(finding_item)
    return out


def reverse_query_next_actions(result: dict[str, Any], report: dict[str, Any]) -> list[str]:
    route_commands = [
        str(route.get("command", ""))
        for route in dict_items(result.get("validation_routes"))
        if route.get("command")
    ]
    return unique_string_items(
        [
            *route_commands,
            *string_items(result.get("commands")),
            *string_items(report.get("commands")),
        ]
    )[:6]


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
        f"watch_addresses={','.join(instruction_trace_related_addresses(report, validation)[:8])}",
        f"trace={instruction_trace_output_path(report)}",
        f"save_state={report.get('effective_save_state') or report.get('save_state', '')}",
        *string_items(report.get("warnings"))[:4],
    ]


def instruction_trace_output_path(report: dict[str, Any]) -> str:
    trace_output = report.get("trace_output") if isinstance(report.get("trace_output"), dict) else {}
    return str(trace_output.get("path") or "")


def instruction_trace_watch_sinks(report: dict[str, Any], validation: dict[str, Any]) -> dict[str, list[str]]:
    symbols: list[str] = []
    addresses: list[str] = []
    address_watch_names: set[str] = set()
    for watch in dict_items(report.get("watches")):
        name = str(watch.get("name") or watch.get("symbol") or watch.get("watch") or "")
        if watch.get("address_watch"):
            if name:
                address_watch_names.add(name)
            address = (
                instruction_trace_address_arg(str(watch.get("raw") or ""))
                or instruction_trace_address_arg(str(watch.get("bank_address") or ""))
                or instruction_trace_address_arg(name)
            )
            if address:
                addresses.append(address)
        elif name:
            symbols.append(name)
    for address in string_items(report.get("watch_addresses")):
        parsed = instruction_trace_address_arg(address)
        if parsed:
            addresses.append(parsed)
    for address in string_items(validation.get("watch_addresses")):
        parsed = instruction_trace_address_arg(address)
        if parsed:
            addresses.append(parsed)
    for watch in string_items(validation.get("watch_symbols")):
        if watch in address_watch_names:
            continue
        address = instruction_trace_address_arg(watch)
        if address:
            addresses.append(address)
        else:
            symbols.append(watch)
    return {
        "symbols": unique_string_items(symbols),
        "addresses": unique_string_items(addresses),
    }


def instruction_trace_address_arg(value: str) -> str:
    text = str(value).strip()
    if not text:
        return ""
    if "=" in text:
        text = text.split("=", 1)[1].strip()
    stripped = text.replace("$", "")
    if stripped.startswith(("0x", "0X")):
        stripped = stripped[2:]
    hex_digits = "0123456789abcdefABCDEF"
    has_address_shape = (
        text.startswith("$")
        or text.startswith(("0x", "0X"))
        or ":" in text
        or (len(stripped) == 4 and all(char in hex_digits for char in stripped))
    )
    return text if has_address_shape else ""


def instruction_trace_related_symbols(report: dict[str, Any], validation: dict[str, Any]) -> list[str]:
    sinks = instruction_trace_watch_sinks(report, validation)
    return unique_string_items(
        [
            *string_items(validation.get("hit_function_symbols")),
            *string_items(validation.get("missing_function_symbols")),
            *sinks["symbols"],
            *[
                str(function.get("symbol", ""))
                for function in dict_items(report.get("functions"))
                if function.get("symbol")
            ],
        ]
    )


def instruction_trace_related_addresses(report: dict[str, Any], validation: dict[str, Any]) -> list[str]:
    return unique_string_items(instruction_trace_watch_sinks(report, validation)["addresses"])


def instruction_trace_dynamic_taint_commands(
    report: dict[str, Any],
    validation: dict[str, Any],
    *,
    trace_path: str,
) -> list[str]:
    commands = []
    sinks = instruction_trace_watch_sinks(report, validation)
    watch_size = instruction_trace_watch_size(report, validation)
    sink_size_arg = f" --sink-size {watch_size}" if watch_size != 1 else ""
    if trace_path:
        commands.append(f"python -m tools.debugger trace-index --trace {trace_path}")
        commands.append(f"python -m tools.debugger minimize --trace {trace_path} --expect event=control_flow")
        for watch in sinks["symbols"][:4]:
            commands.append(
                f"python -m tools.debugger dynamic-taint --trace {trace_path} --sink-symbol {watch} --source-reg <register-or-origin>"
            )
            commands.append(f"python -m tools.debugger expect --trace {trace_path} --expect contains={watch}")
        for address in sinks["addresses"][:4]:
            command_address = command_address_arg(address)
            commands.append(
                f"python -m tools.debugger dynamic-taint --trace {trace_path} --sink-address {command_address}{sink_size_arg} --source-reg <register-or-origin>"
            )
            commands.append(f"python -m tools.debugger expect --trace {trace_path} --expect contains={command_address}")
    commands.extend(string_items(report.get("commands"))[:4])
    return unique_string_items(commands)


def instruction_trace_watch_size(report: dict[str, Any], validation: dict[str, Any]) -> int:
    sizes = []
    for value in (
        report.get("watch_size"),
        report.get("sink_size"),
        validation.get("watch_size"),
        validation.get("sink_size"),
    ):
        size = positive_int(value)
        if size:
            sizes.append(size)
    for watch in dict_items(report.get("watches")):
        size = positive_int(watch.get("watch_size") or watch.get("size"))
        if size:
            sizes.append(size)
    for event in dict_items(report.get("events")):
        size = positive_int(event.get("watch_size") or event.get("sink_size") or event.get("size"))
        if size:
            sizes.append(size)
    return max(sizes) if sizes else 1


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
                evidence=causal_path_evidence(path)[:10],
                next_actions=list(path.get("commands", []))[:4],
            )
        )
    return out


def causal_graph_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for error in report.get("errors", []):
        out.append(
            finding(
                finding_type="ingest_error",
                title="Causal graph setup error",
                source=source,
                severity=SEVERITY_BASE["ingest_error"],
                confidence=0.9,
                evidence=[error],
                next_actions=["Fix graph inputs and rerun `python -m tools.debugger causal-graph`."],
            )
        )
    if not report.get("edge_count", 0):
        out.append(
            finding(
                finding_type="provenance_warning",
                title="Causal graph produced no evidence edges",
                source=source,
                severity=SEVERITY_BASE["provenance_warning"],
                confidence=0.65,
                evidence=list(report.get("warnings", []))[:4]
                or ["Supply watch, effect-trace, reverse-query, dynamic-taint, provenance, or ranked reports."],
                next_actions=["python -m tools.debugger causal-graph --report <debugger-report.json>"],
            )
        )
    for path in report.get("paths", [])[:30]:
        if not isinstance(path, dict):
            continue
        score = int(path.get("score", 0))
        if score < 60:
            continue
        out.append(
            finding(
                finding_type="causal_path",
                title=f"Causal graph path: {path.get('title', '<unknown>')}",
                source=source,
                severity=min(95, score),
                confidence=float(path.get("confidence", 0.6)),
                evidence=causal_path_evidence(path)[:10],
                next_actions=list(path.get("commands", []))[:5] or list(report.get("commands", []))[:5],
                related_symbols=string_items(path.get("related_symbols")),
                related_files=string_items(path.get("related_files")),
                related_addresses=string_items(path.get("related_addresses")),
                proof_status=str(path.get("proof_status") or "planned_only"),
            )
        )
    return out


def causal_path_evidence(path: dict[str, Any]) -> list[str]:
    evidence = string_items(path.get("evidence"))
    summary = path.get("proof_summary") if isinstance(path.get("proof_summary"), dict) else {}
    proof_items: list[str] = []
    min_status = normalize_proof_status(summary.get("min")) if summary else ""
    max_status = normalize_proof_status(summary.get("max")) if summary else ""
    if min_status:
        proof_items.append(f"proof_min={min_status}")
    if max_status:
        proof_items.append(f"proof_max={max_status}")
    edge_count = summary.get("edge_count") if summary else ""
    if edge_count not in {None, ""}:
        proof_items.append(f"proof_edge_count={edge_count}")
    for item in dict_items(path.get("proof_vector"))[:8]:
        relation = str(item.get("relation", ""))
        status = normalize_proof_status(item.get("proof_status"))
        source = str(item.get("source", ""))
        if relation and status:
            suffix = f" source={source}" if source else ""
            proof_items.append(f"proof_edge={relation}:{status}{suffix}")
    return unique_string_items([*evidence, *proof_items])


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
                related_symbols=string_items(target.get("related_symbols"))
                + ([str(target.get("id", ""))] if target.get("type") == "symbol" else []),
                related_files=string_items(target.get("related_files"))
                + ([str(target.get("id", ""))] if target.get("type") == "source_file" else []),
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
        address = event_related_address(event)
        out.append(
            finding(
                finding_type="trace_event",
                title=f"Trace event: {state} {event_type} from {source_symbol}",
                source=source,
                severity=70 if event_type == "watch_change" else 64,
                confidence=float(event.get("confidence", 0.7)),
                evidence=[
                    *list(event.get("evidence", []))[:4],
                    f"source_file={event.get('source_file')}" if event.get("source_file") else "",
                    f"address={address}" if address else "",
                ],
                next_actions=list(event.get("commands", []))[:4] or event_commands(event),
                related_symbols=unique_string_items(
                    [
                        str(event.get("state_symbol", "")),
                        str(event.get("source_symbol", "")),
                        str(event.get("pc_symbol", "")),
                    ]
                ),
                related_files=string_items(event.get("source_file")),
                related_addresses=[address] if address else [],
            )
        )
    for path in report.get("causal_paths", [])[:20]:
        if not isinstance(path, dict):
            continue
        if int(path.get("score", 0)) < 70:
            continue
        proof_status = trace_index_item_proof_status(path, report)
        out.append(
            finding(
                finding_type="causal_path",
                title=f"Trace causal path: {path.get('title', '<unknown>')}",
                source=source,
                severity=min(95, int(path.get("score", 0))),
                confidence=float(path.get("confidence", 0.65)),
                evidence=trace_index_item_evidence(path, proof_status=proof_status),
                next_actions=list(path.get("commands", []))[:4],
                related_symbols=string_items(path.get("related_symbols")),
                related_files=string_items(path.get("related_files")),
                related_addresses=string_items(path.get("related_addresses")),
                proof_status=proof_status,
                evidence_atoms=path.get("evidence_atoms"),
            )
        )
    for item in report.get("reverse_attributions", [])[:20]:
        if not isinstance(item, dict):
            continue
        proof_status = trace_index_item_proof_status(item, report)
        out.append(
            finding(
                finding_type="reverse_attribution",
                title=f"Reverse attribution: {item.get('title', '<unknown>')}",
                source=source,
                severity=72,
                confidence=float(item.get("confidence", 0.65)),
                evidence=trace_index_item_evidence(item, proof_status=proof_status),
                next_actions=list(item.get("commands", []))[:4],
                related_symbols=string_items(item.get("related_symbols")),
                related_files=string_items(item.get("related_files")),
                related_addresses=string_items(item.get("related_addresses")),
                proof_status=proof_status,
                evidence_atoms=item.get("evidence_atoms"),
            )
        )
    return out


def trace_index_item_proof_status(item: dict[str, Any], report: dict[str, Any]) -> str:
    return (
        normalize_proof_status(item.get("proof_status"))
        or normalize_proof_status(report.get("proof_status"))
        or "planned_only"
    )


def trace_index_item_evidence(item: dict[str, Any], *, proof_status: str) -> list[str]:
    evidence = string_items(item.get("evidence"))[:4]
    marker = f"proof_status={proof_status}"
    return unique_string_items([*evidence, marker])


def event_commands(event: dict[str, Any]) -> list[str]:
    commands = []
    for symbol in (event.get("state_symbol"), event.get("source_symbol"), event.get("pc_symbol")):
        if symbol:
            commands.append(f"python -m tools.debugger explain --symbol {symbol}")
    if event.get("address"):
        commands.append(f"python -m tools.debugger trace-index --address {command_address_arg(event.get('address'))}")
    if event.get("rule_id"):
        commands.append(f"python -m tools.debugger coverage --rule {event.get('rule_id')}")
    return commands


def group_status(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("status", ""))
    return str(value or "")


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
            related_symbols = state_patch_minimization_related_symbols(state_patch_minimization)
            related_files = string_items(state_patch_minimization.get("source_files"))
            related_addresses = state_patch_minimization_related_addresses(state_patch_minimization)
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
                        f"semantic_watch={state_patch_minimization.get('semantic_watch_rerun_count', 0)}/{state_patch_minimization.get('semantic_watch_rerun_attempt_count', 0)}",
                        f"semantic_replay={state_patch_minimization.get('semantic_replay_rerun_count', 0)}/{state_patch_minimization.get('semantic_replay_rerun_attempt_count', 0)}",
                        *save_state_delta_evidence(
                            minimized_state_patch_save_state_delta(state_patch_minimization),
                            prefix="minimized_save_state_delta",
                        ),
                        "watch_addresses=" + ",".join(string_items(state_patch_minimization.get("watch_addresses"))[:6]),
                        "source_mems=" + ",".join(string_items(state_patch_minimization.get("source_mems"))[:6]),
                        "semantic_reducer_surfaces=" + ",".join(string_items(state_patch_minimization.get("semantic_reducer_surfaces"))[:6]),
                    ],
                    next_actions=state_patch_minimization_next_actions(state_patch_minimization, source=source)[:10],
                    related_symbols=related_symbols,
                    related_files=related_files,
                    related_addresses=related_addresses,
                )
            )
            for route in dict_items(state_patch_minimization.get("semantic_reducer_routes"))[:12]:
                route_id = str(route.get("id") or route.get("surface") or "semantic_reducer")
                out.append(
                    finding(
                        finding_type="semantic_reducer_route",
                        title=f"Semantic reducer route: {route_id}",
                        source=source,
                        severity=58,
                        confidence=0.76,
                        evidence=[
                            f"surface={route.get('surface', '')}",
                            str(route.get("reason", "")),
                            f"commands={route.get('command_count', 0)}",
                        ],
                        next_actions=string_items(route.get("commands"))[:8],
                        related_symbols=related_symbols,
                        related_files=unique_string_items([*related_files, *string_items(route.get("source_file"))]),
                        related_addresses=related_addresses,
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


def state_patch_minimization_next_actions(item: dict[str, Any], *, source: str) -> list[str]:
    actions = []
    if source:
        actions.extend(
            [
                f"python -m tools.debugger provenance --report {source}",
                f"python -m tools.debugger taint --report {source}",
                f"python -m tools.debugger slice --report {source}",
            ]
        )
    actions.extend(string_items(item.get("commands")))
    out_report = str(item.get("out_report", ""))
    if out_report:
        actions.extend(
            [
                f"python -m tools.debugger setup --report {out_report}",
                f"python -m tools.debugger replay --report {out_report}",
                f"python -m tools.debugger localize --report {out_report}",
                f"python -m tools.debugger coverage --report {out_report}",
            ]
        )
    return unique_string_items(actions)


def state_patch_minimization_related_symbols(item: dict[str, Any]) -> list[str]:
    symbols = [
        *string_items(item.get("symbols")),
        *string_items(item.get("source_symbols")),
        *string_items(item.get("watch_symbols")),
        *source_mem_origins(item),
    ]
    for result in dict_items(item.get("results")):
        symbols.extend(string_items(result.get("semantic_watch_symbols")))
        symbols.extend(string_items(result.get("semantic_replay_watch_symbols")))
        symbols.extend(source_mem_origins(result))
    return unique_string_items(symbols)


def state_patch_minimization_related_addresses(item: dict[str, Any]) -> list[str]:
    addresses = [
        *string_items(item.get("watch_addresses")),
        *source_mem_addresses(item),
    ]
    for result in dict_items(item.get("results")):
        addresses.extend(string_items(result.get("semantic_watch_addresses")))
        addresses.extend(string_items(result.get("semantic_replay_watch_addresses")))
        addresses.extend(source_mem_addresses(result))
    return unique_string_items(addresses)


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
        dynamic_proof = is_dynamic_proof_level(proof_level)
        severity = SEVERITY_BASE["fuzz_campaign"] if dynamic_proof else SEVERITY_BASE["test_gap"]
        finding_type = "fuzz_campaign" if dynamic_proof else "test_gap"
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
                related_symbols=string_items(campaign.get("related_symbols")),
                related_addresses=string_items(campaign.get("related_addresses")),
            )
        )
    for case in report.get("fuzz_cases", [])[:20]:
        if not isinstance(case, dict):
            continue
        if case.get("proof_level") == "dynamic":
            continue
        evidence = string_items(case.get("expectations"))[:4] or string_items(case.get("notes"))[:4]
        if case.get("runtime_targets") or case.get("behavioral_probes") or case.get("state_preconditions"):
            evidence = unique_string_items([*evidence, *content_scenario_evidence(case)[:10]])
        related_symbols = unique_string_items(
            [
                *string_items(case.get("symbols")),
                *string_items(case.get("related_symbols")),
                *content_scenario_related_symbols(case),
            ]
        )
        related_files = unique_string_items(
            [
                *string_items(case.get("changed_file")),
                *content_scenario_related_files(case),
            ]
        )
        related_addresses = unique_string_items(string_items(case.get("related_addresses")))
        proof_level = str(case.get("proof_level", "planning"))
        dynamic_proof = is_dynamic_proof_level(proof_level)
        out.append(
            finding(
                finding_type="fuzz_campaign" if dynamic_proof else "test_gap",
                title=f"{'Dynamic' if dynamic_proof else 'Static'} fuzz case: {case.get('id')}",
                source=source,
                severity=54 if dynamic_proof else 38,
                confidence=0.62,
                evidence=unique_string_items(
                    [
                        f"proof_level={proof_level}",
                        f"counterexample_source={case.get('counterexample_source')}" if case.get("counterexample_source") else "",
                        *evidence,
                    ]
                ),
                next_actions=content_scenario_commands(case)[:12],
                related_symbols=related_symbols,
                related_files=related_files,
                related_addresses=related_addresses,
            )
        )
    return out


def is_dynamic_proof_level(value: Any) -> bool:
    text = str(value)
    return text == "dynamic" or text.startswith("dynamic_") or text.startswith("positioned_state_dynamic")


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
                evidence=[
                    f"surface={item.get('surface', '')}",
                    f"semantic_score={item.get('semantic_score', 0)}",
                    *string_items(item.get("semantic_factors"))[:4],
                    *list(item.get("evidence", []))[:4],
                ],
                next_actions=list(item.get("next_actions", []))[:4],
                related_symbols=string_items(item.get("related_symbols")),
                related_files=string_items(item.get("related_files")),
                related_addresses=string_items(item.get("related_addresses")),
                semantic_factors=string_items(item.get("semantic_factors")),
            )
        )
    return out


def visual_snapshot_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = report_error_findings(report, source=source, title="Visual snapshot setup error")
    surfaces = dict_items(report.get("surfaces")) or dict_items(report.get("planned_surfaces"))
    lcd_state = report.get("lcd_state") if isinstance(report.get("lcd_state"), dict) else {}
    executed = bool(report.get("executed"))
    runtime_samples = visual_snapshot_has_runtime_samples(report)
    proof_status = snapshot_report_proof_status(
        report,
        runtime_samples=runtime_samples,
        downgrade_reason="no_visual_runtime_samples",
    )
    out.append(
        finding(
            finding_type="visual_snapshot",
            title="Visual/UI snapshot captured" if executed else "Visual/UI snapshot planned",
            source=source,
            severity=SEVERITY_BASE["visual_snapshot"] if proof_status == "runtime_observed" else 40,
            confidence=0.78 if proof_status == "runtime_observed" else 0.55,
            evidence=[
                f"executed={executed}",
                f"runtime_samples={runtime_samples}",
                f"surfaces={report.get('surface_count') or len(surfaces)}",
                f"lcd_enabled={lcd_state.get('lcd_enabled')}" if lcd_state else "",
                f"ppu_mode={lcd_state.get('ppu_mode')}" if lcd_state else "",
                f"screen_frames={report.get('screen_frame_count', 0)}",
                f"framebuffer={report.get('framebuffer', '')}" if report.get("framebuffer") else "",
                f"evidence_class={report.get('evidence_class', '')}" if report.get("evidence_class") else "",
                f"hardware_behavior_proven={report.get('hardware_behavior_proven')}"
                if "hardware_behavior_proven" in report
                else "",
                f"hardware_proof_status={report.get('hardware_proof_status', '')}" if report.get("hardware_proof_status") else "",
                f"save_state={report.get('save_state', '')}",
                snapshot_proof_downgrade_evidence(
                    report,
                    runtime_samples=runtime_samples,
                    downgrade_reason="no_visual_runtime_samples",
                ),
            ],
            next_actions=string_items(report.get("commands"))[:8],
            related_symbols=visual_snapshot_symbols(surfaces),
            related_addresses=visual_snapshot_addresses(surfaces),
            proof_status=proof_status,
        )
    )
    return out


def hardware_regression_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = report_error_findings(report, source=source, title="Hardware regression gate input error")
    for case in dict_items(report.get("cases"))[:30]:
        if case.get("hardware_passed"):
            continue
        status = str(case.get("gate_status") or "missing_runtime_hardware_evidence")
        out.append(
            finding(
                finding_type="hardware_regression_blocker",
                title=f"Pan Docs hardware case blocked: {case.get('id', '<case>')}",
                source=source,
                severity=SEVERITY_BASE["hardware_regression_blocker"],
                confidence=0.9,
                evidence=hardware_regression_case_evidence(case),
                next_actions=string_items(report.get("commands"))[:6],
                related_addresses=hardware_regression_case_addresses(case),
                semantic_factors=[f"hardware_case:{case.get('bucket', '')}", f"gate_status:{status}"],
                proof_status=str(case.get("proof_status") or "planned_only"),
            )
        )
    return out


def hardware_regression_case_evidence(case: dict[str, Any]) -> list[str]:
    evidence = [
        f"gate_status={case.get('gate_status', '')}",
        f"hardware_proof_fact_count={case.get('hardware_proof_fact_count', 0)}",
        f"observed_runtime_fact_count={case.get('observed_runtime_fact_count', 0)}",
    ]
    for fact in dict_items(case.get("observed_runtime_facts"))[:4]:
        evidence.extend(hardware_fact_evidence("observed_runtime_fact", fact))
    for fact in dict_items(case.get("hardware_proof_facts"))[:4]:
        evidence.extend(hardware_fact_evidence("hardware_proof_fact", fact))
    for fact in dict_items(case.get("static_blocker_facts"))[:4]:
        evidence.extend(hardware_fact_evidence("static_blocker_fact", fact))
    evidence.extend([
        f"hardware_behavior_proven={case.get('hardware_behavior_proven')}",
        f"static_blocker_count={case.get('static_blocker_count', 0)}",
        f"required_evidence={case.get('required_evidence', '')}",
        (
            "required_event_types=" + ",".join(string_items(case.get("required_event_types")))
            if case.get("required_event_types")
            else ""
        ),
        f"pan_docs_url={case.get('pan_docs_url', '')}",
    ])
    return unique_string_items([item for item in evidence if item and not item.endswith("=")])


def hardware_fact_evidence(prefix: str, fact: dict[str, Any]) -> list[str]:
    return [
        f"{prefix}={fact.get('fact_type', '')}:{fact.get('status', '')}",
        f"{prefix}_proof_scope={fact.get('proof_scope', '')}" if fact.get("proof_scope") else "",
        f"{prefix}_source={fact.get('source', '')}" if fact.get("source") else "",
        (
            f"{prefix}_observed_event_types=" + ",".join(string_items(fact.get("observed_event_types")))
            if fact.get("observed_event_types")
            else ""
        ),
        (
            f"{prefix}_missing_event_types=" + ",".join(string_items(fact.get("missing_event_types")))
            if fact.get("missing_event_types")
            else ""
        ),
    ]


def hardware_regression_case_addresses(case: dict[str, Any]) -> list[str]:
    addresses: list[str] = []
    for item in dict_items(case.get("evidence")):
        detail = str(item.get("detail") or "")
        for raw in detail.replace(";", " ").replace(",", " ").split():
            if raw.startswith("$") and len(raw) in {5, 6}:
                addresses.append(raw)
            elif len(raw) == 4 and all(char in "0123456789abcdefABCDEF" for char in raw):
                addresses.append(raw)
    return unique_string_items(addresses)


def audio_snapshot_findings(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = report_error_findings(report, source=source, title="Audio snapshot setup error")
    symbol_state = dict_items(report.get("symbol_state")) or dict_items(report.get("planned_symbols"))
    register_details = dict_items(report.get("register_details"))
    audio_state = report.get("audio_state") if isinstance(report.get("audio_state"), dict) else {}
    sound_buffer = report.get("sound_buffer") if isinstance(report.get("sound_buffer"), dict) else {}
    executed = bool(report.get("executed"))
    runtime_samples = audio_snapshot_has_runtime_samples(report)
    proof_status = snapshot_report_proof_status(
        report,
        runtime_samples=runtime_samples,
        downgrade_reason="no_audio_runtime_samples",
    )
    out.append(
        finding(
            finding_type="audio_snapshot",
            title="Audio snapshot captured" if executed else "Audio snapshot planned",
            source=source,
            severity=SEVERITY_BASE["audio_snapshot"] if proof_status == "runtime_observed" else 40,
            confidence=0.78 if proof_status == "runtime_observed" else 0.55,
            evidence=[
                f"executed={executed}",
                f"runtime_samples={runtime_samples}",
                f"symbols={report.get('symbol_state_count') or len(symbol_state)}",
                f"registers={report.get('register_count') or len(register_details)}",
                f"audio_enabled={audio_state.get('audio_enabled')}" if audio_state else "",
                f"channel_enable_mask={audio_state.get('channel_enable_mask')}" if audio_state else "",
                f"sound_buffer_source={sound_buffer.get('source')}" if sound_buffer else "",
                f"sound_buffer_sha256={sound_buffer.get('sha256')}" if sound_buffer else "",
                f"evidence_class={report.get('evidence_class', '')}" if report.get("evidence_class") else "",
                f"hardware_behavior_proven={report.get('hardware_behavior_proven')}"
                if "hardware_behavior_proven" in report
                else "",
                f"hardware_proof_status={report.get('hardware_proof_status', '')}" if report.get("hardware_proof_status") else "",
                f"save_state={report.get('save_state', '')}",
                snapshot_proof_downgrade_evidence(
                    report,
                    runtime_samples=runtime_samples,
                    downgrade_reason="no_audio_runtime_samples",
                ),
            ],
            next_actions=string_items(report.get("commands"))[:8],
            related_symbols=audio_snapshot_symbols(
                symbol_state=symbol_state,
                register_details=register_details,
                sound_buffer=sound_buffer,
            ),
            related_addresses=audio_snapshot_addresses(
                symbol_state=symbol_state,
                register_details=register_details,
                wave_ram=report.get("wave_ram") if isinstance(report.get("wave_ram"), dict) else {},
            ),
            proof_status=proof_status,
        )
    )
    return out


def visual_snapshot_has_runtime_samples(report: dict[str, Any]) -> bool:
    screen_frame = report.get("screen_frame") if isinstance(report.get("screen_frame"), dict) else {}
    io_registers = report.get("io_registers") if isinstance(report.get("io_registers"), dict) else {}
    return bool(
        dict_items(report.get("surfaces"))
        or io_registers
        or screen_frame
        or report.get("framebuffer")
        or positive_int(report.get("screen_frame_count"))
    )


def audio_snapshot_has_runtime_samples(report: dict[str, Any]) -> bool:
    registers = report.get("registers") if isinstance(report.get("registers"), dict) else {}
    wave_ram = report.get("wave_ram") if isinstance(report.get("wave_ram"), dict) else {}
    sound_buffer = report.get("sound_buffer") if isinstance(report.get("sound_buffer"), dict) else {}
    return bool(
        registers
        or dict_items(report.get("register_details"))
        or dict_items(report.get("symbol_state"))
        or wave_ram.get("sha256")
        or wave_ram.get("sample_hex")
        or sound_buffer.get("sha256")
        or sound_buffer.get("sample_hex")
        or sound_buffer.get("buffer")
    )


def snapshot_report_proof_status(
    report: dict[str, Any],
    *,
    runtime_samples: bool,
    downgrade_reason: str,
) -> str:
    explicit = normalize_proof_status(report.get("proof_status")) if report.get("proof_status") else ""
    if runtime_samples:
        return explicit or ("runtime_observed" if report.get("executed") else "planned_only")
    if snapshot_proof_downgrade_evidence(
        report,
        runtime_samples=runtime_samples,
        downgrade_reason=downgrade_reason,
    ):
        return "planned_only"
    return explicit or "planned_only"


def snapshot_proof_downgrade_evidence(
    report: dict[str, Any],
    *,
    runtime_samples: bool,
    downgrade_reason: str,
) -> str:
    explicit = normalize_proof_status(report.get("proof_status")) if report.get("proof_status") else ""
    if runtime_samples:
        return ""
    if bool(report.get("executed")) or explicit in {
        "runtime_observed",
        "instruction_observed",
        "taint_proven",
        "mirror_passed",
        "mirror_failed",
    }:
        return f"proof_downgrade_reason={downgrade_reason}"
    return ""


def report_error_findings(report: dict[str, Any], *, source: str, title: str) -> list[dict[str, Any]]:
    return [
        finding(
            finding_type="ingest_error",
            title=title,
            source=source,
            severity=SEVERITY_BASE["ingest_error"],
            confidence=0.9,
            evidence=[error],
            next_actions=string_items(report.get("commands"))[:4],
        )
        for error in string_items(report.get("errors"))[:8]
    ]


def visual_snapshot_symbols(surfaces: list[dict[str, Any]]) -> list[str]:
    return unique_string_items(
        str(surface.get("name") or surface.get("symbol") or "")
        for surface in surfaces
        if surface.get("name") or surface.get("symbol")
    )


def visual_snapshot_addresses(surfaces: list[dict[str, Any]]) -> list[str]:
    return unique_string_items(
        banked_address_text(surface)
        for surface in surfaces
        if surface.get("address")
    )


def audio_snapshot_symbols(
    *,
    symbol_state: list[dict[str, Any]],
    register_details: list[dict[str, Any]],
    sound_buffer: dict[str, Any] | None = None,
) -> list[str]:
    sound = sound_buffer or {}
    return unique_string_items(
        [
            *[
                str(item.get("symbol", ""))
                for item in symbol_state
                if item.get("symbol")
            ],
            *[
                str(item.get("name", ""))
                for item in register_details
                if item.get("name")
            ],
            str(sound.get("source", "")),
        ]
    )


def audio_snapshot_addresses(
    *,
    symbol_state: list[dict[str, Any]],
    register_details: list[dict[str, Any]],
    wave_ram: dict[str, Any],
) -> list[str]:
    return unique_string_items(
        [
            *[
                banked_address_text(item)
                for item in symbol_state
                if item.get("address")
            ],
            *[
                str(item.get("address", ""))
                for item in register_details
                if item.get("address")
            ],
            str(wave_ram.get("address", "")),
        ]
    )


def banked_address_text(item: dict[str, Any]) -> str:
    address = str(item.get("address", ""))
    bank = str(item.get("bank", ""))
    if bank and address:
        return f"{bank}:{address}"
    return address


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
                evidence=[
                    str(item.get("detail", "")),
                    str(item.get("source", "")),
                    f"proof_status={item.get('proof_status')}" if item.get("proof_status") else "",
                ],
                next_actions=[],
                proof_status=str(item.get("proof_status") or ""),
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
    calibrated = with_proof_status(item)
    base_severity = int(calibrated.get("severity", 40))
    proof_adjustment = proof_status_severity_adjustment(str(calibrated.get("proof_status", "")))
    if proof_adjustment:
        calibrated["severity_input"] = base_severity
        calibrated["proof_status_adjustment"] = proof_adjustment
        calibrated["severity"] = clamp_severity(base_severity + proof_adjustment)
        calibrated["evidence"] = unique_string_items(
            [
                *string_items(calibrated.get("evidence")),
                f"Proof status: {calibrated['proof_status']} ({proof_adjustment:+d})",
            ]
        )

    match = first_rom_surface_match(finding_search_text(calibrated))
    if not match:
        return calibrated
    surface_id, surface, bonus = match
    base_severity = int(calibrated.get("severity", 40))
    calibrated["severity_base"] = base_severity
    calibrated["severity_bonus"] = bonus
    calibrated["severity"] = clamp_severity(base_severity + bonus)
    calibrated["surface_id"] = surface_id
    calibrated["surface"] = surface
    calibrated["evidence"] = unique_string_items(
        [
            *string_items(item.get("evidence")),
            f"ROM surface calibration: {surface} (+{bonus})",
        ]
    )
    return calibrated


def with_proof_status(item: dict[str, Any]) -> dict[str, Any]:
    proof_status = normalize_proof_status(item.get("proof_status"))
    if not proof_status:
        proof_status = infer_proof_status(item)
    out = dict(item)
    out["proof_status"] = proof_status
    return out


def normalize_proof_status(value: Any) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "planned": "planned_only",
        "planning": "planned_only",
        "state_patch_planned": "planned_only",
        "runtime_planned": "planned_only",
        "dynamic_trace_planned": "planned_only",
        "dynamic_state_probe_planned": "planned_only",
        "observed": "runtime_observed",
        "runtime": "runtime_observed",
        "instruction": "instruction_observed",
        "taint": "taint_proven",
        "mirror_fail": "mirror_failed",
        "mirror_failure": "mirror_failed",
        "mirror_ok": "mirror_passed",
        "mirror_pass": "mirror_passed",
    }
    text = aliases.get(text, text)
    return text if text in PROOF_STATUSES else ""


def infer_proof_status(item: dict[str, Any]) -> str:
    item_type = str(item.get("type", "")).lower()
    title = str(item.get("title", "")).lower()
    evidence = " ".join(string_items(item.get("evidence"))).lower()
    text = f"{item_type} {title} {evidence}"
    proof_level_status = proof_status_from_proof_level_text(text)
    if proof_level_status:
        return proof_level_status

    if item_type in {"content_mirror_failed", "expectation_failed", "gate_failed"}:
        return "mirror_failed"
    if item_type in {"watch_hit", "workflow_failed", "visual_snapshot", "audio_snapshot"}:
        return "runtime_observed"
    if item_type in {"content_state_executed", "state_space_executed"}:
        return "state_materialized"
    if item_type in {
        "instruction_trace_miss",
        "instruction_trace_partial",
        "instruction_trace_limit",
        "instruction_trace_ready",
    }:
        return "instruction_observed"
    if item_type == "trace_event":
        return "planned_only" if "planned" in title else "instruction_observed"
    if "hit=true" in text or "executed=true" in text or "executed: true" in text:
        return "runtime_observed"
    if "verified=true" in text or "verified: true" in text:
        return "state_materialized"
    if item_type in {"content_mirror_warning", "mirror_passed"}:
        return "mirror_passed"
    return "planned_only"


def proof_status_from_proof_level_text(text: str) -> str:
    if "proof_level" not in text:
        return ""
    if any(marker in text for marker in ("planned", "planning", "runtime_route", "semantic_source", "static_expectation")):
        return "planned_only"
    if "taint" in text:
        return "taint_proven"
    if "dynamic_trace" in text or "instruction" in text:
        return "instruction_observed"
    if "dynamic" in text or "runtime" in text:
        return "runtime_observed"
    return ""


def proof_status_severity_adjustment(proof_status: str) -> int:
    return PROOF_STATUS_SEVERITY_ADJUST.get(normalize_proof_status(proof_status), 0)


def proof_status_score(proof_status: str) -> int:
    return PROOF_STATUS_IMPACT_SCORE.get(normalize_proof_status(proof_status), 0)


def strongest_proof_status(values: list[Any]) -> str:
    statuses = [normalize_proof_status(value) for value in values]
    statuses = [status for status in statuses if status]
    if not statuses:
        return "planned_only"
    return max(statuses, key=lambda status: PROOF_STATUS_RANK.get(status, 0))


def proof_status_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts = {status: 0 for status in PROOF_STATUSES}
    for item in items:
        status = normalize_proof_status(item.get("proof_status")) or infer_proof_status(item)
        counts[status] = counts.get(status, 0) + 1
    return {status: count for status, count in counts.items() if count}


def clamp_severity(value: int) -> int:
    return max(0, min(95, int(value)))


def finding_search_text(item: dict[str, Any]) -> str:
    return " ".join(
        [
            str(item.get("type", "")),
            str(item.get("title", "")),
            " ".join(string_items(item.get("evidence"))),
            " ".join(string_items(item.get("next_actions"))),
            " ".join(string_items(item.get("related_symbols"))),
            " ".join(string_items(item.get("related_files"))),
            " ".join(string_items(item.get("related_addresses"))),
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
    related_symbols: list[str] | None = None,
    related_files: list[str] | None = None,
    related_addresses: list[str] | None = None,
    semantic_factors: list[str] | None = None,
    proof_status: str | None = None,
    evidence_atoms: Any = None,
) -> dict[str, Any]:
    out = {
        "type": finding_type,
        "title": title,
        "source": source,
        "severity": severity,
        "confidence": confidence,
        "evidence": [item for item in evidence if item],
        "next_actions": [item for item in next_actions if item],
        "related_symbols": unique_string_items(related_symbols or []),
        "related_files": unique_string_items(
            normalize_path(item)
            for item in string_items(related_files or [])
        ),
        "related_addresses": unique_string_items(related_addresses or []),
        "semantic_factors": unique_string_items(semantic_factors or []),
        "evidence_atoms": merge_evidence_atoms(evidence_atoms),
    }
    out["proof_status"] = normalize_proof_status(proof_status) or infer_proof_status(out)
    return out


def event_related_address(event: dict[str, Any]) -> str:
    bank_address = str(event.get("bank_address") or "")
    if bank_address:
        return bank_address
    address = event.get("address")
    if isinstance(address, int):
        return f"{address:04X}"
    return str(address or "")


def attribution_related_addresses(attribution: dict[str, Any]) -> list[str]:
    return unique_string_items(
        [
            str(attribution.get("bank_address") or ""),
            str(attribution.get("address") or ""),
            str(attribution.get("sink_address") or ""),
        ]
    )


def attribution_proof_evidence(attribution: dict[str, Any]) -> list[str]:
    keys = (
        "proof_status",
        "match_precision",
        "bank_match",
        "bank_source",
        "proof_downgrade_reason",
        "evidence_source_proof_status",
        "effect_evidence_source",
        "effect_proof_status",
    )
    evidence: list[str] = []
    for key in keys:
        values = string_items(attribution.get(key))
        evidence.extend(f"{key}={value}" for value in values if value)
    return evidence


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


def positive_int(value: Any) -> int:
    try:
        if isinstance(value, int):
            parsed = value
        else:
            text = str(value).strip()
            if not text:
                return 0
            if text.startswith("$"):
                parsed = int(text[1:], 16)
            elif text.startswith(("0x", "0X")):
                parsed = int(text, 16)
            else:
                parsed = int(text, 10)
    except (TypeError, ValueError):
        return 0
    return parsed if parsed > 0 else 0


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


def normalize_path(path: str) -> str:
    return str(path).replace("\\", "/").strip()


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
