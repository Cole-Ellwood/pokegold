from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .catalog import ROOT, triage_request
from .ranking import SEVERITY_BASE, rank_findings
from .reporting import load_reports
from .workflow import command_is_runnable


TYPE_EVIDENCE_BONUS = {
    "gate_failed": 30,
    "ingest_error": 26,
    "save_state_anomaly": 26,
    "workflow_failed": 25,
    "watch_hit": 24,
    "trace_event": 22,
    "reverse_attribution": 23,
    "expectation_failed": 28,
    "localization_candidate": 18,
    "compare_gap": 17,
    "mirror_uncovered": 16,
    "coverage_gap": 12,
    "instruction_trace_miss": 22,
    "instruction_trace_partial": 18,
    "instruction_trace_limit": 18,
    "instruction_trace_ready": 17,
    "generation_route": 14,
    "fuzz_campaign": 15,
    "content_mirror_failed": 22,
    "content_mirror_warning": 8,
    "content_scenario": 11,
    "content_state_blocked": 20,
    "content_state_executed": 18,
    "content_state_ready": 16,
    "state_space_blocked": 20,
    "state_space_executed": 18,
    "state_space_ready": 16,
    "setup_trigger_gap": 18,
    "minimization_route": 12,
    "test_gap": 10,
    "explicit_symbol": 8,
    "explicit_change": 8,
    "symptom": 6,
    "provenance_warning": 4,
    "ingest_warning": 4,
}

SURFACE_HINTS = (
    (
        "banking_abi",
        "ROM banking / ABI",
        38,
        (
            "home/",
            "macros/",
            "farcall",
            "rst ",
            "bankswitch",
            "hrombank",
            "hloadedrombank",
            "stack",
            "register",
            "crash",
            "hang",
            "hl clobber",
            "a clobber",
        ),
    ),
    (
        "boss_ai",
        "Boss AI",
        32,
        (
            "bossai_",
            "wbossai",
            "wenemyaimovescores",
            "bossmodel",
            "boss",
            "boss ai",
            "selector",
            "score",
            "switch",
            "policy",
            "engine/battle/ai/",
            "tools/boss_ai_debugger",
        ),
    ),
    (
        "battle_damage",
        "Battle damage",
        34,
        (
            "wcurdamage",
            "battlecommand_damage",
            "damage",
            "stab",
            "type chart",
            "type matchup",
            "type effectiveness",
            "badge",
            "weather",
            "held item",
            "engine/battle/effect_commands",
            "engine/battle/late_gen_held_items",
            "engine/battle/type_passive_damage_mods",
        ),
    ),
    (
        "battle_core",
        "Battle core",
        28,
        (
            "engine/battle/",
            "battlecommand_",
            "wbattle",
            "wenemy",
            "wplayer",
            "turn",
            "move",
        ),
    ),
    (
        "pokemon_move_data",
        "Pokemon and move data",
        24,
        (
            "data/moves/",
            "data/pokemon/",
            "base_stats",
            "evolutions",
            "learnsets",
            "tmhm",
        ),
    ),
    (
        "maps_scripts_text",
        "Maps, scripts, and text",
        22,
        (
            "maps/",
            "scripts/",
            "text/",
            "warp",
            "object_event",
            "trainer",
            "map",
            "script",
        ),
    ),
    (
        "graphics_audio_ui",
        "Graphics, audio, and UI",
        18,
        (
            "gfx/",
            "audio/",
            "tileset",
            "palette",
            "sprite",
            "song",
            "sfx",
            "menu",
            "window",
        ),
    ),
    (
        "debugger_tooling",
        "Debugger and audit tooling",
        12,
        (
            "tools/debugger",
            "tools/audit",
            "tools/trace",
            "tools/damage_debugger",
        ),
    ),
)
WORD_RE = re.compile(r"[a-z0-9]+")


def build_impact_report(
    *,
    reports: tuple[str, ...] = (),
    changed_files: tuple[str, ...] = (),
    symbols: tuple[str, ...] = (),
    symptom: str = "",
    max_items: int = 40,
    root: Path = ROOT,
) -> dict[str, Any]:
    loaded_reports, load_errors = load_reports(reports=reports, root=root)
    ranked = rank_findings(reports=reports, root=root) if reports else empty_rank_report()

    items: list[dict[str, Any]] = []
    for finding in dict_items(ranked.get("findings")):
        if finding.get("type") == "impact_hotspot":
            continue
        items.append(item_from_finding(finding))
    for loaded in loaded_reports:
        items.extend(items_from_report(loaded["data"], source=loaded["source"]))
    items.extend(input_items(changed_files=changed_files, symbols=symbols, symptom=symptom, root=root))

    impacted = [
        score_item(item)
        for item in merge_items(items)
    ]
    impacted.sort(
        key=lambda item: (
            -int(item["impact_score"]),
            -int(item["severity"]),
            -float(item["confidence"]),
            str(item["surface"]),
            str(item["title"]),
        )
    )
    impacted = impacted[:max_items]
    commands = unique_list(
        command
        for item in impacted
        for command in item.get("next_actions", [])
    )
    errors = unique_list([*load_errors, *ranked.get("errors", [])])
    return {
        "schema_version": 1,
        "kind": "unified_debugger_impact_report",
        "root": str(root),
        "valid": not errors,
        "report_count": len(reports),
        "loaded_report_count": len(loaded_reports),
        "changed_files": list(changed_files),
        "symbols": list(symbols),
        "symptom": symptom,
        "impact_count": len(impacted),
        "error_count": len(errors),
        "errors": errors,
        "items": impacted,
        "command_count": len(commands),
        "commands": commands[:30],
        "runnable_commands": [command for command in commands if command_is_runnable(command)][:30],
        "blocked_commands": [command for command in commands if not command_is_runnable(command)][:30],
        "known_limits": [
            "Impact is a deterministic ROM-aware priority model, not proof of a bug by itself.",
            "Subsystem-specific semantic impact is still strongest for damage and Boss AI until every ROM surface has dynamic mirrors and reducers.",
        ],
    }


def empty_rank_report() -> dict[str, Any]:
    return {"findings": [], "errors": []}


def item_from_finding(finding: dict[str, Any]) -> dict[str, Any]:
    text = " ".join(
        [
            str(finding.get("title", "")),
            " ".join(str(item) for item in finding.get("evidence", [])),
            " ".join(str(item) for item in finding.get("next_actions", [])),
        ]
    )
    related = extract_related(text)
    return impact_item(
        item_type=str(finding.get("type", "ranked_finding")),
        title=normalized_finding_title(finding),
        source=str(finding.get("source", "rank")),
        severity=int(finding.get("severity", 40)),
        confidence=float(finding.get("confidence", 0.5)),
        evidence=string_items(finding.get("evidence")),
        next_actions=string_items(finding.get("next_actions")),
        related_symbols=related["symbols"],
        related_files=related["files"],
    )


def items_from_report(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    kind = report.get("kind", "")
    if kind == "unified_debugger_gate_plan":
        return gate_items(report, source=source)
    if kind == "unified_debugger_watch_report":
        return watch_items(report, source=source)
    if kind == "unified_debugger_coverage_report":
        return coverage_items(report, source=source)
    if kind == "unified_debugger_trace_index":
        return trace_index_items(report, source=source)
    if kind == "unified_debugger_setup_plan":
        return setup_items(report, source=source)
    if kind == "unified_debugger_localization_plan":
        return localization_items(report, source=source)
    if kind == "unified_debugger_minimization_plan":
        return minimization_items(report, source=source)
    if kind == "unified_debugger_generation_plan":
        return generation_items(report, source=source)
    if kind == "unified_debugger_fuzz_plan":
        return fuzz_items(report, source=source)
    if kind == "unified_debugger_compare_plan":
        return compare_items(report, source=source)
    if kind == "unified_debugger_content_mirror":
        return content_mirror_items(report, source=source)
    if kind == "unified_debugger_content_scenarios":
        return content_scenario_items(report, source=source)
    if kind == "unified_debugger_content_state_materialization":
        return content_state_items(report, source=source)
    if kind == "unified_debugger_state_space":
        return state_space_items(report, source=source)
    if kind == "unified_debugger_expectation_report":
        return expectation_items(report, source=source)
    if kind in {"unified_debugger_taint_report", "unified_debugger_dynamic_taint_report"}:
        return taint_items(report, source=source)
    if kind == "unified_debugger_instruction_trace":
        return instruction_trace_items(report, source=source)
    if kind == "unified_debugger_ingest_manifest":
        return ingest_items(report, source=source)
    if kind == "unified_debugger_save_state_inspection":
        return save_state_inspection_items(report, source=source)
    if kind == "unified_debugger_impact_report":
        return nested_impact_items(report, source=source)
    if kind == "unified_debugger_investigation_run":
        return investigation_items(report, source=source)
    return []


def gate_items(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for step in dict_items(report.get("steps")):
        if step.get("status") != "failed":
            continue
        out.append(
            impact_item(
                item_type="gate_failed",
                title=f"Gate failed: {step.get('command', '<unknown-command>')}",
                source=source,
                severity=SEVERITY_BASE["gate_failed"],
                confidence=0.95,
                evidence=[*string_items(step.get("stderr_tail")), *string_items(step.get("stdout_tail"))],
                next_actions=string_items(step.get("command")),
            )
        )
    return out


def watch_items(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for event in dict_items(report.get("events")):
        watch = str(event.get("watch", ""))
        pc_label = str(event.get("pc_label", ""))
        out.append(
            impact_item(
                item_type="watch_hit",
                title=f"{watch} changed at {event.get('pc_bank_address')}",
                source=source,
                severity=SEVERITY_BASE["watch_hit"],
                confidence=0.82,
                evidence=[
                    f"{event.get('old_hex')} -> {event.get('new_hex')}",
                    pc_label,
                    f"context_frames={event.get('dynamic_context', {}).get('context_frame_count', 0)}",
                ],
                next_actions=string_items(event.get("commands")) or string_items(event.get("suggested_commands")),
                related_symbols=[watch, pc_label],
            )
        )
    return out


def taint_items(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for path in dict_items(report.get("paths"))[:20]:
        out.append(
            impact_item(
                item_type="taint_path",
                title=f"Taint path: {path.get('title', path.get('target', '<unknown>'))}",
                source=source,
                severity=min(92, max(SEVERITY_BASE["taint_path"], int(path.get("score", 0)))),
                confidence=float(path.get("confidence", 0.72)),
                evidence=string_items(path.get("evidence"))[:5],
                next_actions=string_items(path.get("commands"))[:5],
                related_symbols=string_items(path.get("related_symbols")),
                related_files=string_items(path.get("related_files")),
            )
        )
    for attribution in dict_items(report.get("write_attributions"))[:20]:
        out.append(
            impact_item(
                item_type="reverse_attribution",
                title=f"Dynamic write: {attribution.get('target', '<sink>')} at {attribution.get('pc_label', '<pc>')}",
                source=source,
                severity=min(92, max(SEVERITY_BASE["reverse_attribution"], int(attribution.get("score", 0)))),
                confidence=float(attribution.get("confidence", 0.72)),
                evidence=string_items(attribution.get("evidence"))[:5],
                next_actions=string_items(attribution.get("commands"))[:5],
                related_symbols=string_items(attribution.get("related_symbols")),
                related_files=string_items(attribution.get("related_files")),
            )
        )
    return out


def instruction_trace_items(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    validation = report.get("execution_validation") if isinstance(report.get("execution_validation"), dict) else {}
    trace_path = instruction_trace_output_path(report)
    if validation.get("attempted") and not validation.get("hit"):
        out.append(
            impact_item(
                item_type="instruction_trace_miss",
                title="Instruction trace executed but selected hooks did not fire",
                source=source,
                severity=SEVERITY_BASE["instruction_trace_miss"] + (6 if validation.get("required") else 0),
                confidence=0.88,
                evidence=instruction_trace_validation_evidence(report, validation),
                next_actions=string_items(report.get("commands"))[:8]
                or ["python -m tools.debugger setup --report <instruction_trace.json>"],
                related_symbols=instruction_trace_related_symbols(report, validation),
            )
        )
    missing_functions = string_items(validation.get("missing_function_symbols"))
    if validation.get("attempted") and validation.get("hit") and missing_functions:
        out.append(
            impact_item(
                item_type="instruction_trace_partial",
                title="Instruction trace missed some selected routines",
                source=source,
                severity=SEVERITY_BASE["instruction_trace_partial"],
                confidence=0.82,
                evidence=instruction_trace_validation_evidence(report, validation),
                next_actions=string_items(report.get("commands"))[:8],
                related_symbols=instruction_trace_related_symbols(report, validation),
            )
        )
    if validation.get("trace_record_limit_hit"):
        out.append(
            impact_item(
                item_type="instruction_trace_limit",
                title="Instruction trace reached the record limit",
                source=source,
                severity=SEVERITY_BASE["instruction_trace_limit"],
                confidence=0.82,
                evidence=instruction_trace_validation_evidence(report, validation),
                next_actions=instruction_trace_limit_commands(report, trace_path=trace_path),
                related_symbols=instruction_trace_related_symbols(report, validation),
            )
        )
    if validation.get("ready_for_dynamic_taint"):
        out.append(
            impact_item(
                item_type="instruction_trace_ready",
                title="Instruction trace is ready for dynamic taint",
                source=source,
                severity=SEVERITY_BASE["instruction_trace_ready"],
                confidence=0.86,
                evidence=instruction_trace_validation_evidence(report, validation),
                next_actions=instruction_trace_dynamic_taint_commands(report, validation, trace_path=trace_path),
                related_symbols=instruction_trace_related_symbols(report, validation),
            )
        )
    for function in dict_items(report.get("functions"))[:12]:
        symbol = str(function.get("symbol", ""))
        out.append(
            impact_item(
                item_type="trace_event",
                title=f"Instruction trace planned for {symbol}",
                source=source,
                severity=56,
                confidence=0.78,
                evidence=[
                    f"instructions={function.get('instruction_count', 0)}",
                    f"hooks={function.get('hook_count', 0)}",
                ],
                next_actions=string_items(report.get("commands"))[:5],
                related_symbols=[symbol],
            )
        )
    return out


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


def instruction_trace_related_symbols(report: dict[str, Any], validation: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            *string_items(validation.get("hit_function_symbols")),
            *string_items(validation.get("missing_function_symbols")),
            *string_items(validation.get("watch_symbols")),
            *[
                str(function.get("symbol", ""))
                for function in dict_items(report.get("functions"))
                if function.get("symbol")
            ],
        ]
    )


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
    return unique_list(commands)


def instruction_trace_limit_commands(report: dict[str, Any], *, trace_path: str) -> list[str]:
    commands = []
    if trace_path:
        commands.append(f"python -m tools.debugger trace-index --trace {trace_path}")
    commands.extend(
        command.replace("--max-frames 50000", "--max-frames 100000")
        for command in string_items(report.get("commands"))[:4]
    )
    return unique_list(commands)


def coverage_items(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for target in dict_items(report.get("uncovered_targets")):
        target_type = str(target.get("type", "target"))
        target_id = str(target.get("id", ""))
        related_symbols: list[str] = []
        related_files: list[str] = []
        if target_type == "symbol":
            related_symbols.append(target_id)
            related_files.extend(string_items(target.get("related_files")))
        elif target_type == "source_file":
            related_files.append(target_id)
            related_symbols.extend(string_items(target.get("related_symbols")))
        out.append(
            impact_item(
                item_type="coverage_gap",
                title=f"Uncovered {target_type}: {target_id}",
                source=source,
                severity=SEVERITY_BASE["coverage_gap"],
                confidence=0.72,
                evidence=[
                    "target was not directly or indirectly observed in provided traces/reports",
                    *string_items(target.get("evidence")),
                ],
                next_actions=string_items(target.get("commands")),
                related_symbols=related_symbols,
                related_files=related_files,
            )
        )
    return out


def trace_index_items(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for event in dict_items(report.get("events"))[:40]:
        event_type = str(event.get("event_type", "trace_event"))
        if event_type not in {"watch_change", "score_delta", "memory_write", "memory_patch"}:
            continue
        state = str(event.get("state_symbol") or event.get("bank_address") or event.get("address") or "state")
        source_symbol = str(event.get("source_symbol") or event.get("pc_symbol") or event.get("rule_id") or "trace")
        out.append(
            impact_item(
                item_type="trace_event",
                title=f"Trace event: {state} {event_type} from {source_symbol}",
                source=source,
                severity=70 if event_type == "watch_change" else 64,
                confidence=float(event.get("confidence", 0.7)),
                evidence=string_items(event.get("evidence")),
                next_actions=event_next_actions(event),
                related_symbols=unique_list(
                    [
                        str(event.get("state_symbol", "")),
                        str(event.get("source_symbol", "")),
                        str(event.get("pc_symbol", "")),
                    ]
                ),
                related_files=string_items(event.get("source_file")),
            )
        )
    for path in dict_items(report.get("causal_paths"))[:20]:
        if int(path.get("score", 0)) < 65:
            continue
        out.append(
            impact_item(
                item_type="causal_path",
                title=f"Trace causal path: {path.get('title', '<unknown>')}",
                source=source,
                severity=min(95, int(path.get("score", 0))),
                confidence=float(path.get("confidence", 0.65)),
                evidence=string_items(path.get("evidence")),
                next_actions=string_items(path.get("commands")),
                related_symbols=string_items(path.get("related_symbols")),
                related_files=string_items(path.get("related_files")),
            )
        )
    for item in dict_items(report.get("reverse_attributions"))[:20]:
        out.append(
            impact_item(
                item_type="reverse_attribution",
                title=f"Reverse attribution: {item.get('title', '<unknown>')}",
                source=source,
                severity=72,
                confidence=float(item.get("confidence", 0.65)),
                evidence=string_items(item.get("evidence")),
                next_actions=string_items(item.get("commands")),
                related_symbols=string_items(item.get("related_symbols")),
                related_files=string_items(item.get("related_files")),
            )
        )
    return out


def event_next_actions(event: dict[str, Any]) -> list[str]:
    commands = []
    for symbol in unique_list(
        [
            str(event.get("state_symbol", "")),
            str(event.get("source_symbol", "")),
            str(event.get("pc_symbol", "")),
        ]
    ):
        commands.append(f"python -m tools.debugger explain --symbol {symbol}")
        commands.append(f"python -m tools.debugger replay --symbol {symbol}")
    if event.get("address"):
        commands.append(f"python -m tools.debugger trace-index --address {event.get('address')}")
    if event.get("rule_id"):
        commands.append(f"python -m tools.debugger coverage --rule {event.get('rule_id')}")
    if event.get("source_file"):
        commands.append(f"python -m tools.debugger gate --changed-file {event.get('source_file')}")
    return unique_list(commands)


def setup_items(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    target_by_surface = {
        str(target.get("surface", "")): target
        for target in dict_items(report.get("targets"))
    }
    coverage = report.get("trigger_coverage")
    coverage_targets = coverage.get("targets", []) if isinstance(coverage, dict) else []
    for row in dict_items(coverage_targets):
        if row.get("status") == "covered":
            continue
        surface = str(row.get("surface", ""))
        target = target_by_surface.get(surface, {})
        blockers = string_items(row.get("blockers"))
        status = str(row.get("status", "planned"))
        out.append(
            impact_item(
                item_type="setup_trigger_gap",
                title=f"Setup trigger {status}: {surface or '<unknown-surface>'}",
                source=source,
                severity=SEVERITY_BASE["setup_trigger_gap"] if status == "blocked" else 52,
                confidence=0.76 if status == "blocked" else 0.66,
                evidence=[
                    f"state={row.get('state_status', '')}",
                    f"trigger={nested_status(row.get('trigger_status'))}",
                    f"validation={nested_status(row.get('validation_status'))}",
                    *blockers,
                ],
                next_actions=string_items(target.get("commands"))[:6]
                or string_items(report.get("commands"))[:6],
                related_symbols=symbols_from_signals(report.get("signals")),
                related_files=files_from_signals(report.get("signals")),
            )
        )
    return out


def localization_items(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    commands = commands_from_phase_steps(report)
    for candidate in dict_items(report.get("candidates"))[:15]:
        candidate_type = str(candidate.get("type", "candidate"))
        candidate_id = str(candidate.get("id", ""))
        score = int(candidate.get("score", 0))
        out.append(
            impact_item(
                item_type="localization_candidate",
                title=f"Localization candidate: {candidate_type} {candidate_id}",
                source=source,
                severity=min(80, 35 + score // 4),
                confidence=min(0.9, 0.45 + score / 250.0),
                evidence=string_items(candidate.get("evidence")),
                next_actions=commands[:6],
                related_symbols=[candidate_id] if candidate_type == "symbol" else [],
                related_files=[candidate_id] if candidate_type == "source_file" else [],
            )
        )
    return out


def minimization_items(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    steps = dict_items(report.get("steps"))
    out: list[dict[str, Any]] = []
    evidence_minimization = report.get("evidence_minimization")
    if isinstance(evidence_minimization, dict) and evidence_minimization.get("preserved"):
        out.append(
            impact_item(
                item_type="minimization_route",
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
    state_patch_minimization = report.get("state_patch_minimization")
    if isinstance(state_patch_minimization, dict) and state_patch_minimization.get("preserved"):
        out.append(
            impact_item(
                item_type="minimization_route",
                title="Content state patches minimized",
                source=source,
                severity=61,
                confidence=0.8,
                evidence=[
                    f"{state_patch_minimization.get('original_patch_count', 0)} -> {state_patch_minimization.get('minimized_patch_count', 0)} patches",
                    f"artifact: {state_patch_minimization.get('out_report', '')}",
                ],
                next_actions=string_items(state_patch_minimization.get("commands")),
                related_symbols=string_items(state_patch_minimization.get("symbols")),
                related_files=string_items(state_patch_minimization.get("source_files")),
            )
        )
    if not steps:
        return out
    surfaces = string_items(report.get("surfaces"))
    selected = string_items(report.get("selected_scenario_ids"))
    bug_ids = string_items(report.get("bug_ids"))
    evidence = []
    if surfaces:
        evidence.append("surfaces: " + ", ".join(surfaces))
    if selected:
        evidence.append("selected scenarios: " + ", ".join(selected[:8]))
    if bug_ids:
        evidence.append("bug ids: " + ", ".join(bug_ids))
    out.append(
        impact_item(
            item_type="minimization_route",
            title="Minimization route is available",
            source=source,
            severity=55,
            confidence=0.75,
            evidence=evidence,
            next_actions=[str(step.get("command", "")) for step in steps],
            related_symbols=symbols_from_signals(report.get("signals")),
            related_files=files_from_signals(report.get("signals")),
        )
    )
    return out


def generation_items(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for generator in dict_items(report.get("generators")):
        status = str(generator.get("status", ""))
        surface = str(generator.get("surface", ""))
        commands = generator_commands(generator)
        if status == "ready":
            out.append(
                impact_item(
                    item_type="generation_route",
                    title=f"Generator route: {generator.get('id', '<unknown>')}",
                    source=source,
                    severity=58,
                    confidence=float(generator.get("confidence", 0.7)),
                    evidence=[
                        f"surface: {surface}",
                        f"seed ids: {len(generator.get('seed_ids', []))}",
                    ],
                    next_actions=commands[:8],
                    related_symbols=symbols_from_signals(report.get("signals")),
                    related_files=files_from_signals(report.get("signals")),
                )
            )
            continue
        out.append(
            impact_item(
                item_type="test_gap",
                title=f"Generator gap: {generator.get('id', '<unknown>')}",
                source=source,
                severity=SEVERITY_BASE["test_gap"],
                confidence=float(generator.get("confidence", 0.55)),
                evidence=string_items(generator.get("gaps")) or [f"status: {status}"],
                next_actions=commands[:8],
                related_symbols=symbols_from_signals(report.get("signals")),
                related_files=files_from_signals(report.get("signals")),
            )
        )
    for counterexample in dict_items(report.get("counterexamples"))[:20]:
        out.append(
            impact_item(
                item_type="generation_route",
                title=f"Counterexample route: {counterexample.get('source', '<unknown>')}",
                source=source,
                severity=52,
                confidence=0.65,
                evidence=[str(counterexample.get("reason", ""))],
                next_actions=string_items(counterexample.get("command")),
                related_symbols=symbols_from_signals(report.get("signals")),
                related_files=files_from_signals(report.get("signals")),
            )
        )
    return out


def generator_commands(generator: dict[str, Any]) -> list[str]:
    commands = []
    for key in ("commands", "counterexample_commands", "materialization_commands"):
        for item in dict_items(generator.get(key)):
            commands.extend(string_items(item.get("command")))
    return unique_list(commands)


def fuzz_items(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for campaign in dict_items(report.get("campaigns")):
        proof_level = str(campaign.get("proof_level", "planning"))
        item_type = "fuzz_campaign" if proof_level == "dynamic" else "test_gap"
        severity = 60 if proof_level == "dynamic" else SEVERITY_BASE["test_gap"]
        out.append(
            impact_item(
                item_type=item_type,
                title=f"Fuzz campaign: {campaign.get('id', '<unknown>')}",
                source=source,
                severity=severity,
                confidence=float(campaign.get("confidence", 0.55)),
                evidence=[
                    f"surface: {campaign.get('surface', '')}",
                    f"proof_level: {proof_level}",
                    *string_items(campaign.get("gaps"))[:3],
                ],
                next_actions=string_items(campaign.get("commands"))[:8],
                related_symbols=string_items(campaign.get("symbols")),
                related_files=string_items(campaign.get("changed_files")),
            )
        )
    for case in dict_items(report.get("fuzz_cases"))[:20]:
        out.append(
            impact_item(
                item_type="fuzz_campaign" if case.get("proof_level") == "dynamic" else "test_gap",
                title=f"Fuzz case: {case.get('id', '<unknown>')}",
                source=source,
                severity=48 if case.get("proof_level") == "dynamic" else 36,
                confidence=0.6,
                evidence=string_items(case.get("expectations"))[:4] or string_items(case.get("notes"))[:4],
                next_actions=string_items(case.get("commands"))[:6],
                related_symbols=string_items(case.get("symbols")),
                related_files=string_items(case.get("changed_file")),
            )
        )
    return out


def compare_items(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for match in dict_items(report.get("matches")):
        for gap in string_items(match.get("gaps")):
            item_type = "mirror_uncovered" if match.get("id") == "uncovered_surface" else "compare_gap"
            out.append(
                impact_item(
                    item_type=item_type,
                    title=f"Mirror gap: {match.get('id', '<unknown>')}",
                    source=source,
                    severity=SEVERITY_BASE[item_type],
                    confidence=0.68,
                    evidence=[gap],
                    next_actions=[
                        *string_items(match.get("commands")),
                        *string_items(match.get("materialization_commands")),
                    ],
                )
            )
    return out


def content_mirror_items(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for error in string_items(report.get("errors")):
        out.append(
            impact_item(
                item_type="ingest_error",
                title="Content mirror input error",
                source=source,
                severity=SEVERITY_BASE["ingest_error"],
                confidence=0.92,
                evidence=[error],
                next_actions=["python -m tools.debugger content-mirror --source-file <changed_file>"],
            )
        )
    for invariant in dict_items(report.get("invariants")):
        status = str(invariant.get("status", ""))
        if status not in {"failed", "warning"}:
            continue
        item_type = "content_mirror_failed" if status == "failed" else "content_mirror_warning"
        out.append(
            impact_item(
                item_type=item_type,
                title=f"Content invariant {status}: {invariant.get('title', invariant.get('id', '<unknown>'))}",
                source=source,
                severity=int(invariant.get("severity", SEVERITY_BASE.get(item_type, 40))),
                confidence=0.86 if status == "failed" else 0.68,
                evidence=string_items(invariant.get("evidence")),
                next_actions=string_items(invariant.get("commands")),
                related_symbols=string_items(invariant.get("related_symbols")),
                related_files=string_items(invariant.get("related_files")) or string_items(invariant.get("source_file")),
            )
        )
    return out


def content_scenario_items(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for error in string_items(report.get("errors")):
        out.append(
            impact_item(
                item_type="ingest_error",
                title="Content scenario input error",
                source=source,
                severity=SEVERITY_BASE["ingest_error"],
                confidence=0.92,
                evidence=[error],
                next_actions=["python -m tools.debugger content-scenarios --source-file <changed_file>"],
            )
        )
    for scenario in dict_items(report.get("scenarios"))[:40]:
        source_file = str(scenario.get("source_file", ""))
        out.append(
            impact_item(
                item_type="content_scenario",
                title=f"Content scenario: {scenario.get('scenario_type', scenario.get('id', '<unknown>'))}",
                source=source,
                severity=46,
                confidence=0.72,
                evidence=[
                    f"{source_file}:{scenario.get('line', 0)}",
                    *string_items(scenario.get("expected"))[:4],
                ],
                next_actions=content_scenario_commands(scenario),
                related_files=[source_file] if source_file else [],
            )
        )
    return out


def content_scenario_commands(scenario: dict[str, Any]) -> list[str]:
    commands = string_items(scenario.get("commands"))
    for probe in dict_items(scenario.get("behavioral_probes")):
        commands.extend(string_items(probe.get("command")))
    return unique_list(commands)


def content_state_items(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    report_commands = string_items(report.get("commands"))
    for error in string_items(report.get("errors")):
        out.append(
            impact_item(
                item_type="ingest_error",
                title="Content state materialization input error",
                source=source,
                severity=SEVERITY_BASE["ingest_error"],
                confidence=0.92,
                evidence=[error],
                next_actions=report_commands[:6]
                or ["python -m tools.debugger content-state --report <content-scenarios.json>"],
            )
        )
    materializations = dict_items(report.get("materializations"))
    if not materializations:
        out.append(
            impact_item(
                item_type="test_gap",
                title="Content state materializer produced no patchable state",
                source=source,
                severity=SEVERITY_BASE["test_gap"],
                confidence=0.65,
                evidence=["Provide a content-scenarios report with map_position state_preconditions."],
                next_actions=report_commands[:6]
                or ["python -m tools.debugger content-state --report <content-scenarios.json>"],
            )
        )
    execution = report.get("execution") if isinstance(report.get("execution"), dict) else {}
    out_state = str(execution.get("out_state") or report.get("out_state") or "")
    for materialization in materializations[:40]:
        status = str(materialization.get("status", "planned"))
        scenario_id = str(materialization.get("scenario_id", "") or materialization.get("precondition_id", ""))
        title_id = scenario_id or str(materialization.get("precondition_kind", "content state"))
        errors = string_items(materialization.get("errors"))
        item_type = "content_state_ready" if status == "ready" and not errors else "content_state_blocked"
        severity = SEVERITY_BASE[item_type]
        if item_type == "content_state_blocked" and not errors and status != "blocked":
            severity = 52
        out.append(
            impact_item(
                item_type=item_type,
                title=content_state_title(status=status, title_id=title_id, item_type=item_type),
                source=source,
                severity=severity,
                confidence=0.78 if item_type == "content_state_ready" else (0.82 if errors else 0.62),
                evidence=[
                    f"scenario={scenario_id}" if scenario_id else "",
                    f"status={status}",
                    f"precondition={materialization.get('precondition_kind', '')}",
                    f"source={materialization.get('source_file', '')}",
                    f"map={materialization.get('map_name', '')}",
                    *content_state_patch_evidence(materialization.get("patches")),
                    *errors[:4],
                    *string_items(materialization.get("notes"))[:4],
                ],
                next_actions=content_state_commands(
                    source=source,
                    materialization=materialization,
                    out_state=out_state,
                    report_commands=report_commands,
                ),
                related_symbols=content_state_patch_symbols(materialization.get("patches")),
                related_files=content_state_related_files(materialization),
            )
        )
    if bool(report.get("executed") or execution.get("executed")):
        applied_patches = dict_items(execution.get("applied_patches"))
        out.append(
            impact_item(
                item_type="content_state_executed",
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
                ),
                related_symbols=content_state_patch_symbols(applied_patches),
                related_files=unique_list(
                    file
                    for materialization in materializations
                    for file in content_state_related_files(materialization)
                ),
            )
        )
    return out


def content_state_title(*, status: str, title_id: str, item_type: str) -> str:
    if item_type == "content_state_ready":
        return f"Content state ready: {title_id}"
    return f"Content state {status}: {title_id}"


def content_state_related_files(materialization: dict[str, Any]) -> list[str]:
    map_resolution = materialization.get("map_resolution") if isinstance(materialization.get("map_resolution"), dict) else {}
    return unique_list(
        normalize_path(path)
        for path in [
            str(materialization.get("source_file", "")),
            str(map_resolution.get("source_file", "")),
        ]
        if path
    )


def content_state_patch_symbols(raw_patches: Any) -> list[str]:
    return unique_list(
        str(patch.get("symbol", ""))
        for patch in dict_items(raw_patches)
        if patch.get("symbol")
    )


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
    commands.extend(
        content_state_watch_command(
            out_state=out_state,
            patch_symbols=content_state_patch_symbols(materialization.get("patches")),
        )
    )
    commands.extend(string_items(materialization.get("commands")))
    commands.extend(report_commands)
    return unique_list(commands)


def content_state_execution_commands(
    *,
    source: str,
    materializations: list[dict[str, Any]],
    out_state: str,
    applied_patches: list[dict[str, Any]],
) -> list[str]:
    commands = [
        f"python -m tools.debugger replay --report {source} --scenario-id {scenario_id} --execute-watch"
        for scenario_id in unique_list(
            str(materialization.get("scenario_id", ""))
            for materialization in materializations
            if materialization.get("scenario_id")
        )[:8]
    ]
    commands.extend(
        content_state_watch_command(
            out_state=out_state,
            patch_symbols=content_state_patch_symbols(applied_patches),
        )
    )
    return unique_list(commands)


def content_state_watch_command(*, out_state: str, patch_symbols: list[str]) -> list[str]:
    symbols = unique_list(symbol for symbol in patch_symbols if symbol)[:6]
    if not out_state or not symbols:
        return []
    return [
        "python -m tools.debugger watch "
        + " ".join(f"--watch-symbol {symbol}" for symbol in symbols)
        + f" --save-state {out_state} --execute"
    ]


def state_space_items(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
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
            impact_item(
                item_type="ingest_error",
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
            impact_item(
                item_type="test_gap",
                title="State-space materializer produced no WRAM patches",
                source=source,
                severity=SEVERITY_BASE["test_gap"],
                confidence=0.65,
                evidence=["Provide at least one --patch SYMBOL=VALUE input."],
                next_actions=report_commands[:6]
                or ["python -m tools.debugger state-space --patch <symbol>=<value>"],
            )
        )
    else:
        item_type = "state_space_blocked" if errors or not report.get("valid", True) else "state_space_ready"
        out.append(
            impact_item(
                item_type=item_type,
                title=(
                    "State-space blocked"
                    if item_type == "state_space_blocked"
                    else f"State-space ready: {scenario_ids[0] if scenario_ids else source}"
                ),
                source=source,
                severity=SEVERITY_BASE[item_type],
                confidence=0.82 if item_type == "state_space_blocked" else 0.78,
                evidence=state_space_evidence(report),
                next_actions=state_space_commands(
                    source=source,
                    scenario_ids=scenario_ids,
                    out_state=out_state,
                    patches=patches,
                    report_commands=report_commands,
                ),
                related_symbols=content_state_patch_symbols(patches),
                related_files=source_files,
            )
        )
    if bool(report.get("executed") or execution.get("executed")):
        applied_patches = dict_items(execution.get("applied_patches")) or [patch for patch in patches if patch.get("applied")]
        out.append(
            impact_item(
                item_type="state_space_executed",
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
                ),
                related_symbols=content_state_patch_symbols(applied_patches or patches),
                related_files=source_files,
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
    return unique_list(
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
    return unique_list(
        [
            *string_items(report.get("source_files")),
            *string_items(state_space.get("source_files")),
            *[
                normalize_path(str(patch.get("source_file", "")))
                for patch in state_space_patch_records(report)
                if patch.get("source_file")
            ],
        ]
    )


def state_space_evidence(report: dict[str, Any]) -> list[str]:
    state_space = report.get("state_space") if isinstance(report.get("state_space"), dict) else {}
    return [
        item
        for item in [
            f"scenario={','.join(state_space_scenario_ids(report))}" if state_space_scenario_ids(report) else "",
            f"source={','.join(state_space_source_files(report))}" if state_space_source_files(report) else "",
            f"patches={len(state_space_patch_records(report))}",
            f"symptom={report.get('symptom') or state_space.get('symptom') or ''}",
            *content_state_patch_evidence(state_space_patch_records(report)),
        ]
        if item
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
    first_symbol = content_state_patch_symbols(patches)[0] if content_state_patch_symbols(patches) else "<symbol>"
    commands.append(
        f"python -m tools.debugger minimize --report {source} --expect state-patch={first_symbol} --out-state-report .local\\tmp\\debugger_state_space_minimized.json"
    )
    commands.extend(report_commands)
    return unique_list(commands)


def expectation_items(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for item in dict_items(report.get("expectations")):
        if item.get("status") != "failed":
            continue
        expectation = item.get("expectation") if isinstance(item.get("expectation"), dict) else {}
        related_symbols = unique_list(
            string_items(expectation.get("symbol"))
            + string_items(expectation.get("state_symbol"))
            + string_items(expectation.get("source_symbol"))
            + string_items(expectation.get("pc_symbol"))
        )
        related_files = string_items(expectation.get("source_file"))
        out.append(
            impact_item(
                item_type="expectation_failed",
                title=f"Expectation failed: {item.get('id', '<unknown>')}",
                source=source,
                severity=int(item.get("severity", SEVERITY_BASE.get("expectation_failed", 78))),
                confidence=0.88,
                evidence=string_items(item.get("evidence")) or [
                    f"observed_count={item.get('observed_count', 0)}"
                ],
                next_actions=string_items(item.get("commands")),
                related_symbols=related_symbols,
                related_files=related_files,
            )
        )
    return out


def ingest_items(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for artifact in dict_items(report.get("artifacts")):
        path = str(artifact.get("path", ""))
        for error in string_items(artifact.get("errors")):
            out.append(
                impact_item(
                    item_type="ingest_error",
                    title=f"Ingest error in {artifact.get('kind')}: {path}",
                    source=source,
                    severity=SEVERITY_BASE["ingest_error"],
                    confidence=0.95,
                    evidence=[error],
                    next_actions=["Fix or regenerate the artifact before replay/localization."],
                    related_files=[path] if path else [],
                )
            )
        for warning in string_items(artifact.get("warnings")):
            out.append(
                impact_item(
                    item_type="ingest_warning",
                    title=f"Ingest warning in {artifact.get('kind')}: {path}",
                    source=source,
                    severity=SEVERITY_BASE["ingest_warning"],
                    confidence=0.7,
                    evidence=[warning],
                    next_actions=["Inspect artifact metadata before trusting downstream output."],
                    related_files=[path] if path else [],
                )
            )
    return out


def save_state_inspection_items(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    related_symbols = ["wScriptBank", "wScriptPos", "wMapScriptsBank", "wEvolutionNewSpecies"]
    for item in dict_items(report.get("findings")):
        severity_level = int(item.get("severity", 3) or 3)
        out.append(
            impact_item(
                item_type="save_state_anomaly",
                title=str(item.get("title") or item.get("id") or "Save-state anomaly"),
                source=source,
                severity={1: 94, 2: 86}.get(severity_level, 35),
                confidence=0.92 if severity_level <= 2 else 0.68,
                evidence=string_items(item.get("detail")) or string_items(item.get("evidence")),
                next_actions=string_items(report.get("commands"))[:5],
                related_symbols=related_symbols,
            )
        )
    return out


def nested_impact_items(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for item in dict_items(report.get("items")):
        copied = dict(item)
        copied["source"] = source
        out.append(copied)
    return out


def investigation_items(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for error in string_items(report.get("errors")):
        out.append(
            impact_item(
                item_type="ingest_error",
                title="Investigation input or step error",
                source=source,
                severity=SEVERITY_BASE["ingest_error"],
                confidence=0.92,
                evidence=[error],
                next_actions=["python -m tools.debugger investigate --json --out-dir <dir>"],
            )
        )
    for step in dict_items(report.get("steps")):
        if step.get("status") != "failed":
            continue
        out.append(
            impact_item(
                item_type="workflow_failed",
                title=f"Investigation step failed: {step.get('id', '<unknown>')} {step.get('title', '')}".strip(),
                source=source,
                severity=SEVERITY_BASE["workflow_failed"],
                confidence=0.9,
                evidence=[
                    *string_items(step.get("errors")),
                    *string_items(step.get("warnings")),
                    f"report: {step.get('report_path', '')}",
                ],
                next_actions=string_items(step.get("commands")),
            )
        )
    for finding in dict_items(report.get("top_findings"))[:20]:
        copied = dict(finding)
        copied["source"] = source
        out.append(item_from_finding(copied))
    for item in dict_items(report.get("top_impact"))[:20]:
        copied = dict(item)
        copied["source"] = source
        out.append(copied)
    if report.get("passed") is False and not out:
        out.append(
            impact_item(
                item_type="workflow_failed",
                title="Investigation did not pass",
                source=source,
                severity=SEVERITY_BASE["workflow_failed"],
                confidence=0.75,
                evidence=[f"failed_count={report.get('failed_count', 0)}"],
                next_actions=string_items(report.get("commands")),
            )
        )
    return out


def input_items(
    *,
    changed_files: tuple[str, ...],
    symbols: tuple[str, ...],
    symptom: str,
    root: Path,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    triage = triage_request(changed_files=changed_files, symptom=symptom, root=root)
    for path in changed_files:
        out.append(
            impact_item(
                item_type="explicit_change",
                title=f"Changed file: {path}",
                source="input",
                severity=42,
                confidence=0.62,
                evidence=["user supplied changed file", *match_notes(triage)],
                next_actions=[
                    f"python -m tools.debugger localize --changed-file {path}",
                    f"python -m tools.debugger coverage --changed-file {path}",
                    f"python -m tools.debugger gate --changed-file {path}",
                ],
                related_files=[path],
            )
        )
    for symbol in symbols:
        out.append(
            impact_item(
                item_type="explicit_symbol",
                title=f"Suspect symbol: {symbol}",
                source="input",
                severity=45,
                confidence=0.65,
                evidence=["user supplied symbol", *match_notes(triage)],
                next_actions=[
                    f"python -m tools.debugger localize --symbol {symbol}",
                    f"python -m tools.debugger coverage --symbol {symbol}",
                    f"python -m tools.debugger slice --symbol {symbol}",
                ],
                related_symbols=[symbol],
            )
        )
    if symptom:
        out.append(
            impact_item(
                item_type="symptom",
                title=f"Symptom: {symptom}",
                source="input",
                severity=38,
                confidence=0.55,
                evidence=match_notes(triage),
                next_actions=[
                    f"python -m tools.debugger localize --symptom {quote_arg(symptom)}",
                    f"python -m tools.debugger gate --symptom {quote_arg(symptom)}",
                    *triage.get("commands", []),
                ],
            )
        )
    return out


def score_item(item: dict[str, Any]) -> dict[str, Any]:
    surface_id, surface, surface_score = infer_surface(item)
    severity = int(item.get("severity", 40))
    item_type = str(item.get("type", ""))
    evidence_bonus = TYPE_EVIDENCE_BONUS.get(item_type, 5)
    proof_bonus = proof_score(string_items(item.get("next_actions")))
    confidence_bonus = round(float(item.get("confidence", 0.0)) * 8)
    score = clamp_score(round(severity * 0.52 + surface_score + evidence_bonus + proof_bonus + confidence_bonus))
    scored = dict(item)
    scored["surface_id"] = surface_id
    scored["surface"] = surface
    scored["surface_score"] = surface_score
    scored["evidence_score"] = evidence_bonus
    scored["proof_score"] = proof_bonus
    scored["impact_score"] = score
    scored["next_actions"] = string_items(scored.get("next_actions"))[:8]
    scored["evidence"] = string_items(scored.get("evidence"))[:8]
    scored["related_symbols"] = unique_list(string_items(scored.get("related_symbols")))[:12]
    scored["related_files"] = unique_list(normalize_path(path) for path in string_items(scored.get("related_files")))[:12]
    return scored


def infer_surface(item: dict[str, Any]) -> tuple[str, str, int]:
    primary_text = " ".join(
        [
            str(item.get("type", "")),
            str(item.get("title", "")),
            " ".join(string_items(item.get("related_symbols"))),
            " ".join(string_items(item.get("related_files"))),
        ]
    ).lower().replace("\\", "/")
    primary_match = first_surface_match(primary_text)
    if primary_match:
        return primary_match

    evidence_text = " ".join(
        [
            primary_text,
            " ".join(string_items(item.get("evidence"))),
        ]
    ).lower().replace("\\", "/")
    evidence_match = first_surface_match(evidence_text)
    if evidence_match:
        return evidence_match
    action_text = " ".join(
        [
            primary_text,
            " ".join(string_items(item.get("next_actions"))),
        ]
    ).lower().replace("\\", "/")
    action_match = first_surface_match(action_text)
    if action_match:
        return action_match
    return "general", "General ROM surface", 10


def first_surface_match(text: str) -> tuple[str, str, int] | None:
    for surface_id, title, score, hints in SURFACE_HINTS:
        if any(hint_matches(hint, text) for hint in hints):
            return surface_id, title, score
    return None


def hint_matches(hint: str, text: str) -> bool:
    normalized = hint.strip()
    if normalized.isalnum():
        return normalized in set(WORD_RE.findall(text))
    return hint in text


def normalized_finding_title(finding: dict[str, Any]) -> str:
    title = str(finding.get("title", "Ranked finding"))
    finding_type = str(finding.get("type", ""))
    if finding_type == "coverage_gap" and title.startswith("Coverage gap: "):
        rest = title.removeprefix("Coverage gap: ")
        parts = rest.split(" ", 1)
        if len(parts) == 2:
            return f"Uncovered {parts[0]}: {parts[1]}"
    return title


def proof_score(commands: list[str]) -> int:
    if any(command_is_runnable(command) for command in commands):
        return 10
    if commands:
        return 4
    return 0


def impact_item(
    *,
    item_type: str,
    title: str,
    source: str,
    severity: int,
    confidence: float,
    evidence: list[str] | None = None,
    next_actions: list[str] | None = None,
    related_symbols: list[str] | None = None,
    related_files: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "type": item_type,
        "title": title,
        "source": source,
        "severity": int(severity),
        "confidence": round(float(confidence), 3),
        "evidence": unique_list(evidence or []),
        "next_actions": unique_list(next_actions or []),
        "related_symbols": unique_list(related_symbols or []),
        "related_files": unique_list(normalize_path(path) for path in (related_files or []) if path),
    }


def merge_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str, str], dict[str, Any]] = {}
    for item in items:
        key = (
            str(item.get("type", "")),
            str(item.get("title", "")),
            str(item.get("source", "")),
        )
        if key not in merged:
            merged[key] = dict(item)
            continue
        existing = merged[key]
        existing["severity"] = max(int(existing.get("severity", 0)), int(item.get("severity", 0)))
        existing["confidence"] = max(float(existing.get("confidence", 0.0)), float(item.get("confidence", 0.0)))
        existing["evidence"] = unique_list([*string_items(existing.get("evidence")), *string_items(item.get("evidence"))])
        existing["next_actions"] = unique_list([*string_items(existing.get("next_actions")), *string_items(item.get("next_actions"))])
        existing["related_symbols"] = unique_list(
            [*string_items(existing.get("related_symbols")), *string_items(item.get("related_symbols"))]
        )
        existing["related_files"] = unique_list(
            [*string_items(existing.get("related_files")), *string_items(item.get("related_files"))]
        )
    return list(merged.values())


def commands_from_phase_steps(report: dict[str, Any]) -> list[str]:
    commands = []
    for step in dict_items(report.get("steps")):
        commands.extend(string_items(step.get("command")))
        commands.extend(string_items(step.get("commands")))
    for phase in dict_items(report.get("phase_steps")):
        for step in dict_items(phase.get("steps")):
            commands.extend(string_items(step.get("command")))
    return unique_list(commands)


def nested_status(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("status", ""))
    return str(value or "")


def symbols_from_signals(value: Any) -> list[str]:
    symbols = []
    for item in dict_items(value):
        if item.get("kind") == "symbol" and item.get("value"):
            symbols.append(str(item["value"]))
    return unique_list(symbols)


def files_from_signals(value: Any) -> list[str]:
    files = []
    for item in dict_items(value):
        if item.get("kind") == "file" and item.get("value"):
            files.append(normalize_path(str(item["value"])))
    return unique_list(files)


def match_notes(triage: dict[str, Any]) -> list[str]:
    return [
        f"triage matched {match.get('id')}: {match.get('reason')}"
        for match in dict_items(triage.get("matches"))
    ]


def extract_related(text: str) -> dict[str, list[str]]:
    symbols: list[str] = []
    files: list[str] = []
    for raw in text.replace("`", " ").replace(",", " ").split():
        token = raw.strip("()[]{}:;\"'")
        if "=" in token:
            _key, value = token.split("=", 1)
            for nested in value.split(","):
                clean = nested.strip("()[]{}:;\"'")
                normalized_nested = normalize_path(clean)
                if "/" in normalized_nested and "." in normalized_nested:
                    files.append(normalized_nested)
                elif looks_like_symbol(clean):
                    symbols.append(clean)
            continue
        normalized = normalize_path(token)
        if "/" in normalized and "." in normalized:
            files.append(normalized)
        elif looks_like_symbol(token):
            symbols.append(token)
    return {"symbols": unique_list(symbols), "files": unique_list(files)}


def looks_like_symbol(token: str) -> bool:
    if len(token) < 3 or len(token) > 80:
        return False
    if token in {"True", "False", "None"}:
        return False
    if token.startswith(("python", "tools", "audit", "json", "unified")):
        return False
    return token[0].isalpha() and any(char.isupper() or char == "_" for char in token)


def quote_arg(value: str) -> str:
    if not value:
        return '""'
    return '"' + value.replace('"', '\\"') + '"'


def normalize_path(path: str) -> str:
    return path.replace("\\", "/").strip()


def clamp_score(value: int) -> int:
    return max(0, min(100, value))


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
    if not isinstance(value, list | tuple):
        return []
    return [item for item in value if isinstance(item, dict)]


def unique_list(values: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value)
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out
