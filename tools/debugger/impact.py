from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .address_boundary import reverse_query_address_boundary_fields
from .catalog import ROOT, triage_request
from .evidence import evidence_atoms, merge_evidence_atoms
from .ranking import (
    PROOF_STATUS_RANK,
    SEVERITY_BASE,
    compare_match_evidence,
    compare_match_proof_status,
    materialized_save_state_delta,
    minimized_state_patch_save_state_delta,
    normalize_proof_status,
    proof_status_counts,
    proof_status_score,
    rank_findings,
    save_state_delta_evidence,
    strongest_proof_status,
    weakest_proof_status,
    with_proof_status,
)
from .reporting import load_reports
from .workflow import command_address_arg, command_is_runnable


TYPE_EVIDENCE_BONUS = {
    "gate_failed": 30,
    "ingest_error": 26,
    "workflow_failed": 25,
    "watch_hit": 24,
    "trace_event": 22,
    "cpu_state_side_effect": 24,
    "visual_snapshot": 16,
    "audio_snapshot": 16,
    "reverse_attribution": 23,
    "effect_trace_post_value_mismatch": 27,
    "effect_trace_unmodeled_change": 25,
    "dynamic_taint_unmodeled_write": 23,
    "expectation_failed": 28,
    "mirror_passed": 3,
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
        "runtime_cpu_state",
        "Runtime execution and CPU state",
        34,
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
        "battle_mechanics_items_hazards",
        "Battle mechanics, items, and hazards",
        33,
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
            "contact",
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
            "visual_snapshot",
            "audio_snapshot",
            "wtilemap",
            "wattrmap",
            "wshadowoam",
            "raud",
            "audio",
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
SEMANTIC_RISK_FACTORS = (
    (
        "cpu_liveness_state",
        "CPU halted/stopped liveness state",
        14,
        (
            "cpu_state",
            "halted",
            "stopped",
            "softlock",
            "freeze",
            "frozen",
            "cpu liveness",
        ),
    ),
    (
        "memory_safety",
        "memory-safety or banked-call risk",
        16,
        (
            "farcall",
            "clobber",
            "hrombank",
            "hloadedrombank",
            "bankswitch",
            "stack",
            "crash",
            "hang",
            "corrupt",
        ),
    ),
    (
        "runtime_rom_proof",
        "ROM-backed runtime state evidence",
        13,
        (
            "watch_hit",
            "trace_event",
            "cpu_state_side_effect",
            "effect_trace",
            "effect_trace_post_value_mismatch",
            "effect_trace_unmodeled_change",
            "post_value_mismatch",
            "unmodeled_observed_change",
            "unattributed",
            "reverse_attribution",
            "dynamic write",
            "pc_bank_address",
            "captured_frames",
            "out_state=",
            "state-patch",
        ),
    ),
    (
        "failed_contract",
        "failed expectation, mirror, or gate contract",
        12,
        (
            "expectation_failed",
            "gate_failed",
            "content_mirror_failed",
            "failed",
            "mismatch",
            "blocked",
            "error",
        ),
    ),
    (
        "battle_mechanics_state",
        "player-visible battle mechanics state",
        12,
        (
            "spikes",
            "rapid spin",
            "hazard",
            "toxic",
            "burn",
            "paralysis",
            "reflect",
            "light screen",
            "safeguard",
            "substitute",
            "weather",
            "held item",
            "air balloon",
            "choice",
            "passive",
        ),
    ),
    (
        "progression_content_state",
        "map, script, trainer, or item progression state",
        8,
        (
            "warp",
            "map",
            "script",
            "trainer",
            "mart",
            "item ball",
            "hidden item",
            "movement",
            "text",
        ),
    ),
    (
        "runtime_probe_route",
        "runtime replay, watch, trace, or materialization route",
        9,
        (
            "behavioral_probe=",
            "content_replay_route",
            "content_runtime_watch_route",
            "content_state_materialization_route",
            "runtime_route=",
            "watch_symbol=",
            "trace_symbol=",
            "--execute",
        ),
    ),
    (
        "script_vm_behavior",
        "script VM, movement, or event-engine behavior",
        10,
        (
            "script_entry",
            "script_command_stream",
            "runscriptcommand",
            "callscript",
            "movement_entry",
            "applymovement",
            "movement_engine",
            "trainer",
            "mart",
            "callasm",
        ),
    ),
    (
        "audiovisual_content_state",
        "graphics, audio, or UI presentation state",
        7,
        (
            "audio_channel",
            "audio_engine_entry",
            "wmusicid",
            "playmusic",
            "gfx/",
            "tileset",
            "palette",
            "sprite",
            "incbin",
            "2bpp",
            "asset",
            "menu",
            "window",
        ),
    ),
    (
        "balance_data_state",
        "Pokemon, move, or trainer balance data",
        7,
        (
            "base_stats",
            "learnsets",
            "evolutions",
            "data/moves",
            "data/pokemon",
            "trainer parties",
            "moveset",
        ),
    ),
)
SEMANTIC_CALIBRATION_PROFILES = (
    (
        "runtime_cpu_state",
        ("runtime_cpu_state",),
        "calibrated CPU liveness runtime severity",
        6,
        ("cpu_liveness_state",),
        ("runtime_rom_proof", "failed_contract"),
        (
            "cpu_state",
            "halted",
            "stopped",
            "softlock",
            "freeze",
            "pc_bank_address",
            "effect trace",
        ),
    ),
    (
        "banking_abi",
        ("banking_abi",),
        "calibrated banking/ABI runtime severity",
        6,
        (),
        ("memory_safety", "runtime_rom_proof", "failed_contract"),
        (
            "gate_failed",
            "expectation_failed",
            "watch_hit",
            "trace_event",
            "reverse_attribution",
            "dynamic write",
            "pc_bank_address",
            "clobber",
            "crash",
            "hang",
        ),
    ),
    (
        "battle_mechanics_items_hazards",
        ("battle_mechanics_items_hazards",),
        "calibrated item/hazard/status mechanics severity",
        5,
        ("battle_mechanics_state",),
        ("runtime_rom_proof", "failed_contract"),
        (
            "gate_failed",
            "expectation_failed",
            "watch_hit",
            "trace_event",
            "reverse_attribution",
            "dynamic write",
            "pc_bank_address",
            "state-patch",
        ),
    ),
    (
        "maps_scripts_text",
        ("maps_scripts_text",),
        "calibrated map/script/text runtime severity",
        5,
        (),
        ("progression_content_state", "script_vm_behavior", "runtime_probe_route", "failed_contract"),
        (
            "content_scenario",
            "content_state_",
            "content_mirror_failed",
            "scenario_type=",
            "precondition=",
            "behavioral_probe=",
            "runtime_route=",
            "watch_symbol=",
            "trace_symbol=",
            "state-patch",
            "trace-instructions",
            "expectation_failed",
            "gate_failed",
            "compare_gap",
        ),
    ),
    (
        "graphics_audio_ui",
        ("graphics_audio_ui",),
        "calibrated graphics/audio/UI runtime severity",
        5,
        (),
        ("audiovisual_content_state", "runtime_probe_route", "failed_contract"),
        (
            "content_scenario",
            "content_state_",
            "content_mirror_failed",
            "audio_engine_entry",
            "audio_channel",
            "behavioral_probe=",
            "runtime_route=",
            "watch_symbol=",
            "trace_symbol=",
            "asset=",
            "incbin",
            "2bpp",
            "expectation_failed",
            "gate_failed",
        ),
    ),
    (
        "pokemon_move_data",
        ("pokemon_move_data",),
        "calibrated Pokemon/move-data gameplay severity",
        4,
        (),
        ("balance_data_state", "failed_contract", "runtime_probe_route"),
        (
            "content_scenario",
            "content_state_",
            "content_mirror_failed",
            "expectation_failed",
            "gate_failed",
            "compare_gap",
            "state-patch",
        ),
    ),
)


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

    learning_profiles = impact_learning_profiles(loaded_reports)
    impacted = [
        score_item(item)
        for item in merge_items(items)
    ]
    if learning_profiles:
        impacted = [apply_learned_impact(item, learning_profiles) for item in impacted]
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
        "proof_status_counts": proof_status_counts(impacted),
        "learned_profile_count": len(learning_profiles),
        "error_count": len(errors),
        "errors": errors,
        "items": impacted,
        "command_count": len(commands),
        "commands": commands[:30],
        "runnable_commands": [command for command in commands if command_is_runnable(command)][:30],
        "blocked_commands": [command for command in commands if not command_is_runnable(command)][:30],
        "known_limits": [
            "Impact ranking is prioritization, not proof of a bug by itself.",
            "Learned impact priors only apply when supplied feedback reports match a surface plus concrete file, symbol, item type, or semantic factor evidence.",
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
    item = impact_item(
        item_type=str(finding.get("type", "ranked_finding")),
        title=normalized_finding_title(finding),
        source=str(finding.get("source", "rank")),
        severity=int(finding.get("severity", 40)),
        confidence=float(finding.get("confidence", 0.5)),
        evidence=string_items(finding.get("evidence")),
        next_actions=string_items(finding.get("next_actions")),
        related_symbols=unique_list(
            [*string_items(finding.get("related_symbols")), *related["symbols"]]
        ),
        related_files=unique_list(
            [*string_items(finding.get("related_files")), *related["files"]]
        ),
        related_addresses=string_items(finding.get("related_addresses")),
        proof_status=str(finding.get("proof_status", "")),
        evidence_atoms=finding.get("evidence_atoms"),
    )
    item.update(reverse_query_address_boundary_fields(finding))
    return item


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
        address = event_related_address(event)
        out.append(
            impact_item(
                item_type="watch_hit",
                title=f"{watch} changed at {event.get('pc_bank_address')}",
                source=source,
                severity=SEVERITY_BASE["watch_hit"],
                confidence=0.82,
                evidence=[
                    f"{event.get('old_hex')} -> {event.get('new_hex')}",
                    f"address={address}" if address else "",
                    pc_label,
                    f"context_frames={event.get('dynamic_context', {}).get('context_frame_count', 0)}",
                ],
                next_actions=string_items(event.get("commands")) or string_items(event.get("suggested_commands")),
                related_symbols=unique_list([symbol_if_not_address(watch), pc_label]),
                related_addresses=[address] if address else [],
            )
        )
    return out


def taint_items(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for route in trace_synthesis_routes(report)[:20]:
        out.append(
            impact_item(
                item_type="trace_synthesis_planned",
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
                related_addresses=string_items(path.get("related_addresses")),
                proof_status=str(path.get("proof_status") or ""),
                evidence_atoms=path.get("evidence_atoms"),
            )
        )
    for attribution in dict_items(report.get("write_attributions"))[:20]:
        addresses = attribution_related_addresses(attribution)
        out.append(
            impact_item(
                item_type="reverse_attribution",
                title=f"Dynamic write: {attribution.get('target', '<sink>')} at {attribution.get('pc_label', '<pc>')}",
                source=source,
                severity=min(92, max(SEVERITY_BASE["reverse_attribution"], int(attribution.get("score", 0)))),
                confidence=float(attribution.get("confidence", 0.72)),
                evidence=[
                    *string_items(attribution.get("evidence"))[:5],
                    *attribution_proof_evidence(attribution),
                    *[f"address={address}" for address in addresses],
                ],
                next_actions=string_items(attribution.get("commands"))[:5],
                related_symbols=string_items(attribution.get("related_symbols")),
                related_files=string_items(attribution.get("related_files")),
                related_addresses=addresses,
                proof_status=str(attribution.get("proof_status") or ""),
                evidence_atoms=attribution.get("evidence_atoms"),
            )
        )
    return out


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
    return unique_list(
        [
            *string_items(route.get("sink_symbols")),
            *string_items(route.get("source_symbols")),
            *source_mem_origins(route),
        ]
    )


def trace_synthesis_related_addresses(route: dict[str, Any]) -> list[str]:
    return unique_addresses(
        [
            *string_items(route.get("sink_addresses")),
            *source_mem_addresses(route),
        ]
    )


def source_mem_origins(route: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            origin
            for _, origin in source_mem_parts(route)
            if origin
        ]
    )


def source_mem_addresses(route: dict[str, Any]) -> list[str]:
    return unique_list(
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
                related_addresses=instruction_trace_related_addresses(report, validation),
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
                related_addresses=instruction_trace_related_addresses(report, validation),
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
                related_addresses=instruction_trace_related_addresses(report, validation),
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
                related_addresses=instruction_trace_related_addresses(report, validation),
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
        "symbols": unique_list(symbols),
        "addresses": unique_addresses(addresses),
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
    return unique_list(
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
    return unique_addresses(instruction_trace_watch_sinks(report, validation)["addresses"])


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
    return unique_list(commands)


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
        address = event_related_address(event)
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
                related_addresses=[address] if address else [],
            )
        )
    for path in dict_items(report.get("causal_paths"))[:20]:
        if int(path.get("score", 0)) < 65:
            continue
        proof_status = trace_index_item_proof_status(path, report)
        out.append(
            impact_item(
                item_type="causal_path",
                title=f"Trace causal path: {path.get('title', '<unknown>')}",
                source=source,
                severity=min(95, int(path.get("score", 0))),
                confidence=float(path.get("confidence", 0.65)),
                evidence=trace_index_item_evidence(path, proof_status=proof_status),
                next_actions=string_items(path.get("commands")),
                related_symbols=string_items(path.get("related_symbols")),
                related_files=string_items(path.get("related_files")),
                related_addresses=string_items(path.get("related_addresses")),
                proof_status=proof_status,
                evidence_atoms=path.get("evidence_atoms"),
            )
        )
    for item in dict_items(report.get("reverse_attributions"))[:20]:
        proof_status = trace_index_item_proof_status(item, report)
        out.append(
            impact_item(
                item_type="reverse_attribution",
                title=f"Reverse attribution: {item.get('title', '<unknown>')}",
                source=source,
                severity=72,
                confidence=float(item.get("confidence", 0.65)),
                evidence=trace_index_item_evidence(item, proof_status=proof_status),
                next_actions=string_items(item.get("commands")),
                related_symbols=string_items(item.get("related_symbols")),
                related_files=string_items(item.get("related_files")),
                related_addresses=string_items(item.get("related_addresses")),
                proof_status=proof_status,
                evidence_atoms=item.get("evidence_atoms"),
            )
        )
    return out


def trace_index_item_proof_status(item: dict[str, Any], report: dict[str, Any]) -> str:
    explicit = normalize_proof_status(item.get("proof_status")) if item.get("proof_status") else ""
    if explicit:
        return explicit
    atom_statuses = [
        normalize_proof_status(atom.get("proof_status"))
        for atom in evidence_atoms(item.get("evidence_atoms"))
        if atom.get("proof_status")
    ]
    if atom_statuses:
        return weakest_proof_status(atom_statuses)
    return normalize_proof_status(report.get("proof_status")) or "planned_only"


def trace_index_item_evidence(item: dict[str, Any], *, proof_status: str) -> list[str]:
    evidence = string_items(item.get("evidence"))
    marker = f"proof_status={proof_status}"
    return unique_list([*evidence, marker])


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
        commands.append(f"python -m tools.debugger trace-index --address {command_address_arg(event.get('address'))}")
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
                related_addresses=[candidate_id] if candidate_type == "address" else [],
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
        related_symbols = state_patch_minimization_related_symbols(state_patch_minimization)
        related_files = string_items(state_patch_minimization.get("source_files"))
        related_addresses = state_patch_minimization_related_addresses(state_patch_minimization)
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
                next_actions=state_patch_minimization_next_actions(state_patch_minimization, source=source),
                related_symbols=related_symbols,
                related_files=related_files,
                related_addresses=related_addresses,
            )
        )
        for route in dict_items(state_patch_minimization.get("semantic_reducer_routes"))[:12]:
            route_id = str(route.get("id") or route.get("surface") or "semantic_reducer")
            out.append(
                impact_item(
                    item_type="semantic_reducer_route",
                    title=f"Semantic reducer route: {route_id}",
                    source=source,
                    severity=57,
                    confidence=0.74,
                    evidence=[
                        f"surface={route.get('surface', '')}",
                        str(route.get("reason", "")),
                        f"commands={route.get('command_count', 0)}",
                    ],
                    next_actions=string_items(route.get("commands")),
                    related_symbols=related_symbols,
                    related_files=unique_list([*related_files, *string_items(route.get("source_file"))]),
                    related_addresses=related_addresses,
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
    return unique_list(actions)


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
        dynamic_proof = is_dynamic_proof_level(proof_level)
        item_type = "fuzz_campaign" if dynamic_proof else "test_gap"
        severity = 60 if dynamic_proof else SEVERITY_BASE["test_gap"]
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
                related_symbols=unique_list(
                    [
                        *string_items(campaign.get("symbols")),
                        *string_items(campaign.get("related_symbols")),
                    ]
                ),
                related_files=string_items(campaign.get("changed_files")),
                related_addresses=string_items(campaign.get("related_addresses")),
            )
        )
    for case in dict_items(report.get("fuzz_cases"))[:20]:
        evidence = string_items(case.get("expectations"))[:4] or string_items(case.get("notes"))[:4]
        if case.get("runtime_targets") or case.get("behavioral_probes") or case.get("state_preconditions"):
            evidence = unique_list([*evidence, *content_scenario_evidence(case)[:10]])
        related_symbols = unique_list(
            [
                *string_items(case.get("symbols")),
                *string_items(case.get("related_symbols")),
                *content_scenario_related_symbols(case),
            ]
        )
        related_files = unique_list(
            [
                *string_items(case.get("changed_file")),
                *content_scenario_related_files(case),
            ]
        )
        proof_level = str(case.get("proof_level", "planning"))
        dynamic_proof = is_dynamic_proof_level(proof_level)
        out.append(
            impact_item(
                item_type="fuzz_campaign" if dynamic_proof else "test_gap",
                title=f"Fuzz case: {case.get('id', '<unknown>')}",
                source=source,
                severity=48 if dynamic_proof else 36,
                confidence=0.6,
                evidence=unique_list(
                    [
                        f"proof_level={proof_level}",
                        f"counterexample_source={case.get('counterexample_source')}" if case.get("counterexample_source") else "",
                        *evidence,
                    ]
                ),
                next_actions=content_scenario_commands(case)[:12],
                related_symbols=related_symbols,
                related_files=related_files,
                related_addresses=string_items(case.get("related_addresses")),
            )
        )
    return out


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
    return unique_list(symbols)


def state_patch_minimization_related_addresses(item: dict[str, Any]) -> list[str]:
    addresses = [
        *string_items(item.get("watch_addresses")),
        *source_mem_addresses(item),
    ]
    for result in dict_items(item.get("results")):
        addresses.extend(string_items(result.get("semantic_watch_addresses")))
        addresses.extend(string_items(result.get("semantic_replay_watch_addresses")))
        addresses.extend(source_mem_addresses(result))
    return unique_addresses(addresses)


def is_dynamic_proof_level(value: Any) -> bool:
    text = str(value)
    return text == "dynamic" or text.startswith("dynamic_") or text.startswith("positioned_state_dynamic")


def compare_items(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out = []
    for match in dict_items(report.get("matches")):
        if match.get("status") == "passed":
            proof_status = compare_match_proof_status(match)
            out.append(
                impact_item(
                    item_type="mirror_passed",
                    title=f"Mirror passed: {match.get('id', '<unknown>')}",
                    source=source,
                    severity=SEVERITY_BASE["mirror_passed"],
                    confidence=0.82,
                    evidence=compare_match_evidence(match, proof_status=proof_status),
                    next_actions=string_items(match.get("commands"))[:4],
                    related_symbols=string_items(match.get("related_symbols")),
                    related_files=string_items(match.get("source_files")),
                    related_addresses=string_items(match.get("related_addresses")),
                    proof_status=proof_status,
                )
            )
        for gap in string_items(match.get("gaps")):
            item_type = "mirror_uncovered" if match.get("id") == "uncovered_surface" else "compare_gap"
            out.append(
                impact_item(
                    item_type=item_type,
                    title=f"Mirror gap: {match.get('id', '<unknown>')}",
                    source=source,
                    severity=SEVERITY_BASE[item_type],
                    confidence=0.68,
                    evidence=[gap, *string_items(match.get("evidence"))[:4]],
                    next_actions=[
                        *string_items(match.get("commands")),
                        *string_items(match.get("materialization_commands")),
                    ],
                    related_symbols=string_items(match.get("related_symbols")),
                    related_files=string_items(match.get("source_files")),
                    related_addresses=string_items(match.get("related_addresses")),
                    proof_status=str(match.get("proof_status") or ""),
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
                evidence=content_scenario_evidence(scenario),
                next_actions=content_scenario_commands(scenario),
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
    for probe in dict_items(scenario.get("behavioral_probes")):
        probe_commands.extend(string_items(probe.get("command")))
    commands.extend(probe_commands)
    commands.extend(string_items(scenario.get("commands")))
    return unique_list(commands)


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
    return unique_list(item for item in out if item)


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
    return unique_list(symbol for symbol in symbols if symbol)


def content_scenario_related_files(scenario: dict[str, Any]) -> list[str]:
    runtime_targets = scenario.get("runtime_targets") if isinstance(scenario.get("runtime_targets"), dict) else {}
    files = [
        str(scenario.get("source_file", "")),
        *string_items(scenario.get("related_files")),
        *string_items(runtime_targets.get("source_files")),
    ]
    for probe in dict_items(scenario.get("behavioral_probes")):
        files.extend(string_items(probe.get("source_file")))
    return unique_list(normalize_path(path) for path in files if path)


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
                    *save_state_delta_evidence(materialized_save_state_delta(report)),
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
                    *save_state_delta_evidence(materialized_save_state_delta(report)),
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
    item = with_proof_status(item)
    surface_id, surface, surface_score = infer_surface(item)
    severity = int(item.get("severity", 40))
    item_type = str(item.get("type", ""))
    evidence_bonus = TYPE_EVIDENCE_BONUS.get(item_type, 5)
    proof_status = str(item.get("proof_status", "planned_only"))
    proof_bonus = proof_score(string_items(item.get("next_actions"))) + proof_status_score(proof_status)
    semantic_bonus, semantic_factors = semantic_risk_profile(item, surface_id=surface_id)
    confidence_bonus = round(float(item.get("confidence", 0.0)) * 8)
    score = clamp_score(
        round(
            severity * 0.48
            + surface_score
            + evidence_bonus
            + proof_bonus
            + min(24, semantic_bonus)
            + confidence_bonus
        )
    )
    scored = dict(item)
    scored["surface_id"] = surface_id
    scored["surface"] = surface
    scored["surface_score"] = surface_score
    scored["evidence_score"] = evidence_bonus
    scored["proof_status"] = proof_status
    scored["proof_score"] = proof_bonus
    scored["semantic_score"] = semantic_bonus
    scored["semantic_factors"] = semantic_factors
    scored["semantic_calibration_profiles"] = semantic_profile_ids(semantic_factors)
    scored["learned_impact_score"] = 0
    scored["learned_impact_profiles"] = []
    scored["impact_score"] = score
    scored["next_actions"] = string_items(scored.get("next_actions"))[:12]
    scored["evidence"] = string_items(scored.get("evidence"))[:8]
    scored["evidence_atoms"] = merge_evidence_atoms(scored.get("evidence_atoms"), limit=12)
    scored["related_symbols"] = unique_list(string_items(scored.get("related_symbols")))[:12]
    scored["related_files"] = unique_list(normalize_path(path) for path in string_items(scored.get("related_files")))[:12]
    scored["related_addresses"] = unique_addresses(string_items(scored.get("related_addresses")))[:12]
    return scored


def semantic_risk_profile(item: dict[str, Any], *, surface_id: str) -> tuple[int, list[str]]:
    text = impact_search_text(item, include_evidence=True)
    score = 0
    factors: list[str] = []
    for factor_id, label, bonus, hints in SEMANTIC_RISK_FACTORS:
        if any(hint_matches(hint, text) for hint in hints):
            score += bonus
            factors.append(f"{factor_id}: {label} (+{bonus})")
    if surface_id == "battle_mechanics_items_hazards" and not any(
        factor.startswith("battle_mechanics_state:") for factor in factors
    ):
        score += 8
        factors.append("battle_mechanics_state: player-visible battle mechanics state (+8)")
    calibration_score, calibration_factors = semantic_calibration_profile(
        surface_id=surface_id,
        text=text,
        factors=factors,
    )
    score += calibration_score
    factors.extend(calibration_factors)
    return score, factors


def semantic_calibration_profile(
    *,
    surface_id: str,
    text: str,
    factors: list[str],
) -> tuple[int, list[str]]:
    factor_ids = semantic_factor_ids(factors)
    score = 0
    out: list[str] = []
    for (
        profile_id,
        surface_ids,
        label,
        bonus,
        required_all_factors,
        required_any_factors,
        evidence_hints,
    ) in SEMANTIC_CALIBRATION_PROFILES:
        if surface_id not in surface_ids:
            continue
        if required_all_factors and not set(required_all_factors).issubset(factor_ids):
            continue
        if required_any_factors and factor_ids.isdisjoint(required_any_factors):
            continue
        if evidence_hints and not any(hint_matches(hint, text) for hint in evidence_hints):
            continue
        score += bonus
        out.append(f"semantic_calibration:{profile_id}: {label} (+{bonus})")
    return score, out


def semantic_factor_ids(factors: list[str]) -> set[str]:
    return {factor.split(":", 1)[0] for factor in factors if factor}


def semantic_profile_ids(factors: list[str]) -> list[str]:
    out: list[str] = []
    for factor in factors:
        parts = factor.split(":", 2)
        if len(parts) >= 2 and parts[0] == "semantic_calibration":
            out.append(parts[1])
    return unique_list(out)


def impact_learning_profiles(loaded_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    profiles: list[dict[str, Any]] = []
    for loaded in loaded_reports:
        report = loaded.get("data")
        if not isinstance(report, dict) or not report.get("valid", True):
            continue
        raw_profiles: list[dict[str, Any]] = []
        if report.get("kind") == "unified_debugger_impact_feedback":
            raw_profiles.extend(dict_items(report.get("outcomes")))
            raw_profiles.extend(dict_items(report.get("profiles")))
            raw_profiles.extend(dict_items(report.get("feedback")))
        raw_profiles.extend(dict_items(report.get("impact_feedback")))
        for index, raw in enumerate(raw_profiles, start=1):
            profile = normalize_impact_learning_profile(raw, source=str(loaded.get("source", "")), index=index)
            if profile:
                profiles.append(profile)
    return profiles


def normalize_impact_learning_profile(raw: dict[str, Any], *, source: str, index: int) -> dict[str, Any] | None:
    bonus = learned_impact_bonus(raw)
    if bonus == 0:
        return None
    surface_id = normalize_surface_id(str(raw.get("surface_id") or raw.get("surface") or ""))
    profile = {
        "id": str(raw.get("id") or raw.get("name") or f"{source}#{index}"),
        "source": source,
        "surface_id": surface_id,
        "bonus": bonus,
        "confidence": clamp_float(raw.get("confidence", 0.75), minimum=0.0, maximum=1.0),
        "outcome": str(raw.get("outcome") or raw.get("status") or "feedback"),
        "evidence": string_items(raw.get("evidence"))[:4],
        "item_types": set(string_items(raw.get("item_types")) or string_items(raw.get("types"))),
        "symbols": set(string_items(raw.get("symbols")) or string_items(raw.get("related_symbols"))),
        "file_prefixes": tuple(
            normalize_path(path)
            for path in (
                string_items(raw.get("file_prefixes"))
                or string_items(raw.get("path_prefixes"))
                or string_items(raw.get("source_files"))
                or string_items(raw.get("related_files"))
                or string_items(raw.get("source_file"))
            )
        ),
        "semantic_factor_ids": set(
            factor_id_from_text(factor)
            for factor in (
                string_items(raw.get("semantic_factor_ids"))
                or string_items(raw.get("factor_ids"))
                or string_items(raw.get("semantic_factors"))
            )
            if factor_id_from_text(factor)
        ),
        "semantic_profiles": set(
            string_items(raw.get("semantic_calibration_profiles"))
            or string_items(raw.get("calibration_profiles"))
        ),
        "title_keywords": tuple(keyword.lower() for keyword in string_items(raw.get("title_keywords"))),
    }
    has_match_constraint = any(
        [
            profile["item_types"],
            profile["symbols"],
            profile["file_prefixes"],
            profile["semantic_factor_ids"],
            profile["semantic_profiles"],
            profile["title_keywords"],
        ]
    )
    return profile if surface_id and has_match_constraint else None


def learned_impact_bonus(raw: dict[str, Any]) -> int:
    explicit = signed_int(
        raw.get("impact_bonus")
        or raw.get("severity_bonus")
        or raw.get("impact_delta")
        or raw.get("score_delta")
    )
    if explicit:
        return max(-12, min(12, explicit))
    outcome = str(raw.get("outcome") or raw.get("status") or "").lower()
    if any(word in outcome for word in ("false_positive", "not_a_bug", "dismissed")):
        return -8
    if any(word in outcome for word in ("blocker", "softlock", "crash")):
        return 12
    if any(word in outcome for word in ("confirmed", "regression", "playtest")):
        return 8
    if "minor" in outcome:
        return 3
    return 0


def apply_learned_impact(item: dict[str, Any], profiles: list[dict[str, Any]]) -> dict[str, Any]:
    matched = [profile for profile in profiles if impact_learning_profile_matches(item, profile)]
    if not matched:
        scored = dict(item)
        scored["learned_impact_score"] = 0
        scored["learned_impact_profiles"] = []
        return scored
    learned_score = max(-18, min(18, round(sum(profile["bonus"] * profile["confidence"] for profile in matched))))
    scored = dict(item)
    scored["learned_impact_score"] = learned_score
    scored["learned_impact_profiles"] = [profile["id"] for profile in matched]
    scored["impact_score"] = clamp_score(int(scored.get("impact_score", 0)) + learned_score)
    scored["evidence"] = unique_list(
        [
            *string_items(scored.get("evidence")),
            *(
                f"learned_impact={profile['id']} outcome={profile['outcome']} ({learned_score:+d})"
                for profile in matched[:3]
            ),
        ]
    )[:8]
    return scored


def impact_learning_profile_matches(item: dict[str, Any], profile: dict[str, Any]) -> bool:
    if profile["surface_id"] != item.get("surface_id"):
        return False
    if profile["item_types"] and str(item.get("type", "")) not in profile["item_types"]:
        return False
    item_symbols = set(string_items(item.get("related_symbols")))
    if profile["symbols"] and item_symbols.isdisjoint(profile["symbols"]):
        return False
    item_files = [normalize_path(path) for path in string_items(item.get("related_files"))]
    if profile["file_prefixes"] and not any(
        item_file == prefix or item_file.startswith(prefix.rstrip("/") + "/")
        for item_file in item_files
        for prefix in profile["file_prefixes"]
    ):
        return False
    item_factor_ids = semantic_factor_ids(string_items(item.get("semantic_factors")))
    if profile["semantic_factor_ids"] and item_factor_ids.isdisjoint(profile["semantic_factor_ids"]):
        return False
    item_profiles = set(string_items(item.get("semantic_calibration_profiles")))
    if profile["semantic_profiles"] and item_profiles.isdisjoint(profile["semantic_profiles"]):
        return False
    title = str(item.get("title", "")).lower()
    if profile["title_keywords"] and not any(keyword in title for keyword in profile["title_keywords"]):
        return False
    return True


def normalize_surface_id(value: str) -> str:
    text = value.strip().lower()
    if not text:
        return ""
    for surface_id, title, _score, _hints in SURFACE_HINTS:
        if text in {surface_id.lower(), title.lower()}:
            return surface_id
    return text if any(surface_id == text for surface_id, _title, _score, _hints in SURFACE_HINTS) else ""


def factor_id_from_text(value: str) -> str:
    text = str(value).strip()
    return text.split(":", 1)[0] if text else ""


def infer_surface(item: dict[str, Any]) -> tuple[str, str, int]:
    primary_text = impact_search_text(item, include_evidence=False)
    primary_match = first_surface_match(primary_text)
    if primary_match:
        return primary_match

    evidence_text = impact_search_text(item, include_evidence=True)
    evidence_match = first_surface_match(evidence_text)
    if evidence_match:
        return evidence_match
    action_text = impact_search_text(item, include_evidence=True, include_actions=True)
    action_match = first_surface_match(action_text)
    if action_match:
        return action_match
    return "general", "General ROM surface", 10


def impact_search_text(
    item: dict[str, Any],
    *,
    include_evidence: bool,
    include_actions: bool = False,
) -> str:
    parts = [
        str(item.get("type", "")),
        str(item.get("title", "")),
        " ".join(string_items(item.get("related_symbols"))),
        " ".join(string_items(item.get("related_files"))),
        " ".join(string_items(item.get("related_addresses"))),
    ]
    if include_evidence:
        parts.append(" ".join(string_items(item.get("evidence"))))
    if include_actions:
        parts.append(" ".join(string_items(item.get("next_actions"))))
    return " ".join(parts).lower().replace("\\", "/")


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
    related_addresses: list[str] | None = None,
    proof_status: str | None = None,
    evidence_atoms: Any = None,
) -> dict[str, Any]:
    out = {
        "type": item_type,
        "title": title,
        "source": source,
        "severity": int(severity),
        "confidence": round(float(confidence), 3),
        "evidence": unique_list(evidence or []),
        "next_actions": unique_list(next_actions or []),
        "related_symbols": unique_list(related_symbols or []),
        "related_files": unique_list(normalize_path(path) for path in (related_files or []) if path),
        "related_addresses": unique_addresses(related_addresses or []),
        "evidence_atoms": merge_evidence_atoms(evidence_atoms),
    }
    return with_proof_status({**out, "proof_status": proof_status or ""})


def proof_status_sort_key(status: str) -> tuple[int, str]:
    return (PROOF_STATUS_RANK.get(status, 0), status)


def normalized_proof_status_values(*values: Any) -> list[str]:
    statuses: list[str] = []
    for value in values:
        for raw in string_items(value):
            for part in raw.replace(";", ",").split(","):
                status = normalize_proof_status(part.strip())
                if status:
                    statuses.append(status)
    return sorted(unique_list(statuses), key=proof_status_sort_key)


def item_proof_statuses(item: dict[str, Any]) -> list[str]:
    statuses = normalized_proof_status_values(
        item.get("proof_status"),
        item.get("proof_statuses"),
        item.get("proof_min"),
        item.get("proof_max"),
    )
    by_source = item.get("proof_status_by_source")
    if isinstance(by_source, dict):
        statuses = normalized_proof_status_values(statuses, list(by_source.values()))
    return statuses


def merge_proof_status_by_source(existing: dict[str, Any], item: dict[str, Any]) -> dict[str, str]:
    merged: dict[str, str] = {}
    for source_map in (existing.get("proof_status_by_source"), item.get("proof_status_by_source")):
        if not isinstance(source_map, dict):
            continue
        for source, status_value in source_map.items():
            source_key = str(source or "").strip()
            status = normalize_proof_status(status_value)
            if not source_key or not status:
                continue
            if source_key in merged:
                status = strongest_proof_status([merged[source_key], status])
            merged[source_key] = status
    return {source: merged[source] for source in sorted(merged)}


def merged_proof_vector(existing: dict[str, Any], item: dict[str, Any]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[tuple[tuple[str, str], ...]] = set()
    for entry in [*dict_items(existing.get("proof_vector")), *dict_items(item.get("proof_vector"))]:
        key = tuple(sorted((str(field), str(value)) for field, value in entry.items()))
        if key in seen:
            continue
        seen.add(key)
        merged.append(dict(entry))
    return merged


def apply_mixed_proof_summary(item: dict[str, Any], statuses: list[str]) -> None:
    if len(statuses) <= 1:
        return
    proof_min = min(statuses, key=proof_status_sort_key)
    proof_max = strongest_proof_status(statuses)
    item["proof_statuses"] = statuses
    item["proof_min"] = proof_min
    item["proof_max"] = proof_max
    item["proof_badge"] = "mixed"
    item["evidence"] = unique_list(
        [
            *string_items(item.get("evidence")),
            f"proof_statuses={','.join(statuses)}",
            f"proof_min={proof_min}",
            f"proof_max={proof_max}",
        ]
    )


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
        existing["related_addresses"] = unique_addresses(
            [*string_items(existing.get("related_addresses")), *string_items(item.get("related_addresses"))]
        )
        existing["evidence_atoms"] = merge_evidence_atoms(existing.get("evidence_atoms"), item.get("evidence_atoms"))
        source_statuses = merge_proof_status_by_source(existing, item)
        if source_statuses:
            existing["proof_status_by_source"] = source_statuses
        proof_vector = merged_proof_vector(existing, item)
        if proof_vector:
            existing["proof_vector"] = proof_vector
        proof_statuses = normalized_proof_status_values(
            item_proof_statuses(existing),
            item_proof_statuses(item),
            list(source_statuses.values()),
        )
        existing["proof_status"] = strongest_proof_status(proof_statuses)
        apply_mixed_proof_summary(existing, proof_statuses)
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


def signed_int(value: Any) -> int:
    try:
        if isinstance(value, int):
            return value
        text = str(value).strip()
        if not text:
            return 0
        if text.startswith("$"):
            return int(text[1:], 16)
        if text.startswith(("0x", "0X")):
            return int(text, 16)
        return int(text, 10)
    except (TypeError, ValueError):
        return 0


def clamp_float(value: Any, *, minimum: float, maximum: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = minimum
    return max(minimum, min(maximum, parsed))


def dict_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [item for item in value if isinstance(item, dict)]


def event_related_address(event: dict[str, Any]) -> str:
    bank_address = str(event.get("bank_address") or "")
    if bank_address:
        return bank_address
    address = event.get("address")
    if isinstance(address, int):
        return f"{address:04X}"
    return str(address or "")


def symbol_if_not_address(value: str) -> str:
    text = str(value).strip()
    if not text:
        return ""
    stripped = text.replace("$", "")
    if ":" in stripped:
        stripped = stripped.split(":", 1)[1]
    if stripped.startswith(("0x", "0X")):
        stripped = stripped[2:]
    if len(stripped) == 4 and all(char in "0123456789abcdefABCDEF" for char in stripped):
        return ""
    return text


def attribution_related_addresses(attribution: dict[str, Any]) -> list[str]:
    return unique_addresses(
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


def unique_addresses(values: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if not text:
            continue
        key = text.upper().replace("$", "")
        if ":" in key:
            key = key.split(":", 1)[1]
        key = key[-4:] if len(key) >= 4 else key
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
    return out


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
