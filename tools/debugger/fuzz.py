from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .catalog import ROOT
from .content_scenarios import (
    attach_behavioral_probes,
    content_scenario_records,
    content_state_instruction_trace_command,
)
from .generate import (
    BANKING_TRACE_SYMBOLS,
    BANKING_WATCH_SYMBOLS,
    banking_dynamic_probe_commands,
    banking_patch_expectations,
    banking_patch_profile,
    banking_state_space_request,
    build_generation_plan,
    execute_command_batch,
)
from .localize import normalize_path
from .provenance import display_path, resolve_path
from .workflow import command_is_runnable, command_parts


CONTENT_MACROS = (
    "warp_event",
    "object_event",
    "bg_event",
    "coord_event",
    "def_warp_events",
    "def_object_events",
    "def_bg_events",
    "def_coord_events",
    "map_header",
    "INCBIN",
    "pic",
    "tilemap",
    "musicheader",
    "channel_count",
)
SURFACE_PROOF_LEVEL = {
    "damage": "dynamic",
    "boss_ai": "dynamic",
    "banking_abi": "dynamic_state_probe_planned",
    "content_static": "positioned_state_dynamic_planned",
    "general": "planning",
}
LABEL_RE = re.compile(r"^\s*([A-Za-z_.$][A-Za-z0-9_.$]*)(?:::|:)")


def build_fuzz_plan(
    *,
    reports: tuple[str, ...] = (),
    scenarios: tuple[str, ...] = (),
    families: tuple[str, ...] = (),
    symbols: tuple[str, ...] = (),
    changed_files: tuple[str, ...] = (),
    symptom: str = "",
    out_cases: str = "",
    max_cases: int = 64,
    seed: int = 1,
    execute: bool = False,
    max_execute_commands: int = 8,
    execute_timeout_seconds: int = 600,
    root: Path = ROOT,
) -> dict[str, Any]:
    case_limit = max(1, int(max_cases))
    warnings = []
    if max_cases < 1:
        warnings.append("max_cases was below 1 and was clamped to 1")

    generation = build_generation_plan(
        reports=reports,
        scenarios=scenarios,
        families=families,
        symbols=symbols,
        changed_files=changed_files,
        symptom=symptom,
        max_cases=case_limit,
        seed=seed,
        root=root,
    )
    campaigns = build_campaigns(
        generation=generation,
        changed_files=changed_files,
        symbols=symbols,
        symptom=symptom,
        max_cases=case_limit,
        seed=seed,
        root=root,
    )
    fuzz_scenario_manifest_path = (
        display_path(resolve_path(out_cases, root=root), root=root)
        if out_cases else "<fuzz_cases.jsonl>"
    )
    cases = build_fuzz_cases(
        campaigns=campaigns,
        changed_files=changed_files,
        symbols=symbols,
        symptom=symptom,
        max_cases=case_limit,
        seed=seed,
        scenario_manifest_path=fuzz_scenario_manifest_path,
        root=root,
    )
    case_output = write_case_records(records=cases, out_cases=out_cases, root=root)
    commands = unique_list(
        [
            *generation.get("commands", []),
            *[
                command
                for campaign in campaigns
                for command in campaign.get("commands", [])
            ],
            *[
                command
                for case in cases
                for command in case.get("commands", [])
            ],
        ]
    )
    execution = execute_command_batch(
        commands,
        execute=execute,
        max_commands=max_execute_commands,
        timeout_seconds=execute_timeout_seconds,
        root=root,
        step_prefix="fuzz",
    )
    errors = unique_list(
        [
            *generation.get("errors", []),
            *case_output.get("errors", []),
            *(execution.get("errors", []) if execute else []),
        ]
    )
    return {
        "schema_version": 1,
        "kind": "unified_debugger_fuzz_plan",
        "root": str(root),
        "valid": not errors,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "reports": list(reports),
        "scenarios": list(scenarios),
        "changed_files": list(changed_files),
        "symbols": list(symbols),
        "families": list(families),
        "symptom": symptom,
        "seed": seed,
        "max_cases": case_limit,
        "surface_count": len(generation.get("surfaces", [])),
        "surfaces": generation.get("surfaces", []),
        "campaign_count": len(campaigns),
        "dynamic_campaign_count": sum(1 for campaign in campaigns if is_dynamic_proof_level(campaign.get("proof_level"))),
        "static_campaign_count": sum(1 for campaign in campaigns if str(campaign.get("proof_level", "")).startswith("static")),
        "counterexample_campaign_count": sum(1 for campaign in campaigns if campaign.get("source") == "generation_counterexample"),
        "dynamic_taint_handoff_count": generation.get("dynamic_taint_handoff_count", 0),
        "campaigns": campaigns,
        "fuzz_case_count": len(cases),
        "fuzz_cases": cases[:case_limit],
        "case_manifest": case_output,
        "generation_plan": {
            "generator_count": generation.get("generator_count", 0),
            "surfaces": generation.get("surfaces", []),
            "seed_count": generation.get("seed_count", 0),
            "dynamic_taint_handoff_count": generation.get("dynamic_taint_handoff_count", 0),
        },
        "command_count": len(commands),
        "commands": commands,
        "runnable_commands": [command for command in commands if command_is_runnable(command)],
        "blocked_commands": [command for command in commands if not command_is_runnable(command)],
        "executed": execute,
        "execution": execution,
        "known_limits": [
            "This is a unified fuzz campaign planner; it only executes bounded campaign commands when --execute is supplied.",
            "Damage and Boss AI campaigns route to dynamic fuzzers; content/map campaigns now route to positioned-state materialization plus replay.",
            "Ready instruction-trace reports become dynamic-taint handoff campaigns and fuzz cases so captured ROM execution can drive sink attribution without manual path copying.",
            "Content fuzz cases prove source invariants immediately; runtime behavior is proven after a base state is materialized into the generated content-state report.",
        ],
    }


def build_campaigns(
    *,
    generation: dict[str, Any],
    changed_files: tuple[str, ...],
    symbols: tuple[str, ...],
    symptom: str,
    max_cases: int,
    seed: int,
    root: Path,
) -> list[dict[str, Any]]:
    campaigns = []
    for handoff in dict_items(generation.get("dynamic_taint_handoffs")):
        command = str(handoff.get("command", ""))
        campaigns.append(
            {
                "id": f"fuzz_{handoff.get('id', 'instruction_trace_dynamic_taint')}",
                "surface": "instruction_trace",
                "title": "Instruction trace dynamic-taint handoff",
                "proof_level": "dynamic_trace",
                "status": handoff.get("status", "ready"),
                "confidence": 0.78,
                "seed": seed,
                "case_budget": max_cases,
                "changed_files": [normalize_path(path) for path in changed_files],
                "symbols": list(symbols),
                "symptom": symptom,
                "commands": unique_list([command]),
                "gaps": [],
                "source_report": str(handoff.get("source_report", "")),
                "trace_count": int(handoff.get("trace_count", 0)),
                "traces": list(handoff.get("traces", [])),
                "sink_symbols": list(handoff.get("sink_symbols", [])),
                "sink_addresses": list(handoff.get("sink_addresses", [])),
                "source_regs": list(handoff.get("source_regs", [])),
                "source_mems": list(handoff.get("source_mems", [])),
                "source_symbols": list(handoff.get("source_symbols", [])),
                "related_symbols": dynamic_taint_related_symbols(handoff),
                "related_addresses": dynamic_taint_related_addresses(handoff),
            }
        )
    campaigns.extend(
        generation_counterexample_campaigns(
            generation=generation,
            changed_files=changed_files,
            symbols=symbols,
            symptom=symptom,
            max_cases=max_cases,
            seed=seed,
        )
    )
    for generator in dict_items(generation.get("generators")):
        surface = str(generator.get("surface", "general"))
        proof_level = str(generator.get("proof_level") or SURFACE_PROOF_LEVEL.get(surface, "planning"))
        commands = command_strings(generator.get("commands"))
        commands.extend(command_strings(generator.get("counterexample_commands")))
        if surface == "content_static":
            commands.extend(content_probe_commands(changed_files=changed_files, root=root))
        if surface == "banking_abi":
            commands.extend(banking_dynamic_probe_commands(report_stem=".local\\tmp\\debugger_banking_campaign"))
            commands.append("python -m tools.debugger taint --symbol hROMBank")
        campaigns.append(
            {
                "id": f"fuzz_{generator.get('id', surface)}",
                "surface": surface,
                "title": fuzz_title(generator),
                "proof_level": proof_level,
                "status": generator.get("status", "planned"),
                "confidence": generator.get("confidence", 0.5),
                "seed": seed,
                "case_budget": max_cases,
                "changed_files": [normalize_path(path) for path in changed_files],
                "symbols": list(symbols),
                "symptom": symptom,
                "commands": unique_list(commands),
                "gaps": list(generator.get("gaps", [])),
                "related_symbols": unique_list([*symbols, *BANKING_WATCH_SYMBOLS, *BANKING_TRACE_SYMBOLS]) if surface == "banking_abi" else [],
            }
        )
    if campaigns:
        return campaigns
    return [
        {
            "id": "fuzz_general_baseline",
            "surface": "general",
            "title": "General debugger fuzz baseline",
            "proof_level": "planning",
            "status": "needs-subsystem",
            "confidence": 0.35,
            "seed": seed,
            "case_budget": max_cases,
            "changed_files": [normalize_path(path) for path in changed_files],
            "symbols": list(symbols),
            "symptom": symptom,
            "commands": [
                "python -m tools.debugger triage --symptom <description>",
                "python -m tools.debugger generate --symptom <description>",
                "python -m tools.debugger compare --changed-file <changed_file>",
            ],
            "gaps": ["No surface-specific fuzz campaign matched these inputs."],
        }
    ]


def generation_counterexample_campaigns(
    *,
    generation: dict[str, Any],
    changed_files: tuple[str, ...],
    symbols: tuple[str, ...],
    symptom: str,
    max_cases: int,
    seed: int,
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for item in dict_items(generation.get("counterexamples")):
        command = str(item.get("command", ""))
        if not command:
            continue
        source = str(item.get("source") or "counterexample")
        if source != "suggest-tests":
            continue
        if not is_unified_debugger_route_counterexample(command):
            continue
        group = grouped.setdefault(
            source,
            {
                "commands": [],
                "reasons": [],
                "related_symbols": [],
                "related_addresses": [],
            },
        )
        group["commands"].append(command)
        reason = str(item.get("reason", ""))
        if reason:
            group["reasons"].append(reason)
        group["related_symbols"].extend(string_items(item.get("related_symbols")))
        group["related_addresses"].extend(string_items(item.get("related_addresses")))

    campaigns = []
    for source, group in grouped.items():
        commands = unique_list(group["commands"])
        surface = infer_counterexample_surface(commands)
        related_symbols = unique_list(
            [
                *command_flag_values(commands, ("--sink-symbol", "--watch-symbol", "--symbol", "--source-symbol")),
                *string_items(group.get("related_symbols")),
            ]
        )
        related_addresses = unique_list(
            [
                *source_mem_or_address_values(
                    command_flag_values(commands, ("--sink-address", "--watch-address", "--address", "--source-mem"))
                ),
                *source_mem_or_address_values(string_items(group.get("related_addresses"))),
            ]
        )
        campaigns.append(
            {
                "id": f"fuzz_{slug_id(source)}_{slug_id(surface)}_counterexamples",
                "surface": surface,
                "title": f"{source} counterexample campaign",
                "proof_level": infer_counterexample_proof_level(commands),
                "status": "planned",
                "confidence": 0.72,
                "seed": seed,
                "case_budget": max_cases,
                "changed_files": [normalize_path(path) for path in changed_files],
                "symbols": list(symbols),
                "symptom": symptom,
                "commands": commands,
                "gaps": [],
                "source": "generation_counterexample",
                "counterexample_source": source,
                "counterexample_reasons": unique_list(group["reasons"]),
                "related_symbols": related_symbols,
                "related_addresses": related_addresses,
            }
        )
    return campaigns


def is_unified_debugger_route_counterexample(command: str) -> bool:
    return (
        "tools.debugger content-state" in command
        or "tools.debugger trace-instructions" in command
        or "tools.debugger dynamic-taint" in command
    )


def infer_counterexample_surface(commands: list[str]) -> str:
    text = "\n".join(commands)
    if "dynamic-taint" in text or "trace-instructions" in text:
        return "instruction_trace"
    if "tools.damage_debugger" in text:
        return "damage"
    if "tools.boss_ai_debugger" in text:
        return "boss_ai"
    if "content-state" in text or "content-mirror" in text or "content-scenarios" in text:
        return "content_static"
    if "check_cross_bank_call.py" in text or "hROMBank" in text:
        return "banking_abi"
    return "counterexample"


def infer_counterexample_proof_level(commands: list[str]) -> str:
    text = "\n".join(commands)
    if "dynamic-taint" in text or "trace-instructions" in text:
        return "dynamic_trace_planned"
    if "--execute" in text or " replay " in text:
        return "dynamic_planned"
    if "content-state" in text:
        return "positioned_state_dynamic_planned"
    return "planning"


def command_flag_values(commands: list[str], flags: tuple[str, ...]) -> list[str]:
    values: list[str] = []
    for command in commands:
        tokens = command_parts(command)
        for index, token in enumerate(tokens):
            for flag in flags:
                if token == flag and index + 1 < len(tokens):
                    values.append(clean_flag_value(tokens[index + 1]))
                elif token.startswith(flag + "="):
                    values.append(clean_flag_value(token.split("=", 1)[1]))
    return unique_list(values)


def clean_flag_value(value: str) -> str:
    return str(value).strip().strip("'\"")


def dynamic_taint_related_symbols(data: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            *string_items(data.get("related_symbols")),
            *string_items(data.get("sink_symbols")),
            *string_items(data.get("source_symbols")),
            *source_mem_origins(data),
        ]
    )


def dynamic_taint_related_addresses(data: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            *source_mem_or_address_values(string_items(data.get("related_addresses"))),
            *string_items(data.get("sink_addresses")),
            *source_mem_addresses(data),
        ]
    )


def source_mem_origins(data: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            origin
            for _, origin in source_mem_parts(data)
            if origin
        ]
    )


def source_mem_addresses(data: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            address
            for address, _ in source_mem_parts(data)
            if address
        ]
    )


def source_mem_or_address_values(values: list[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        parts = source_mem_parts({"source_mems": [value]})
        if parts and parts[0][0]:
            out.append(parts[0][0])
        else:
            out.append(value)
    return out


def source_mem_parts(data: dict[str, Any]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for value in string_items(data.get("source_mems")):
        text = str(value).strip()
        if not text:
            continue
        if "=" in text:
            left, right = (part.strip() for part in text.split("=", 1))
            if looks_like_address(left):
                out.append((left, right))
            elif looks_like_address(right):
                out.append((right, left))
            else:
                out.append((left, right))
        else:
            out.append((text, ""))
    return out


def looks_like_address(value: str) -> bool:
    text = str(value).strip().replace("$", "")
    if ":" in text:
        bank, address = text.split(":", 1)
        return is_hex(bank, 2) and is_hex(address, 4)
    return is_hex(text, 4)


def is_hex(value: str, length: int) -> bool:
    text = str(value).strip()
    return len(text) == length and all(char in "0123456789abcdefABCDEF" for char in text)


def build_fuzz_cases(
    *,
    campaigns: list[dict[str, Any]],
    changed_files: tuple[str, ...],
    symbols: tuple[str, ...],
    symptom: str,
    max_cases: int,
    seed: int,
    scenario_manifest_path: str,
    root: Path,
) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    ordered_campaigns = sorted(campaigns, key=lambda item: 0 if item.get("surface") == "instruction_trace" else 1)
    for campaign in ordered_campaigns:
        surface = str(campaign.get("surface", "general"))
        if campaign.get("source") == "generation_counterexample":
            cases.extend(generation_counterexample_cases(campaign=campaign, seed=seed))
        elif surface == "content_static":
            cases.extend(
                content_fuzz_cases(
                    campaign=campaign,
                    changed_files=changed_files,
                    max_cases=max_cases,
                    seed=seed,
                    scenario_manifest_path=scenario_manifest_path,
                    root=root,
                )
            )
        elif surface == "banking_abi":
            cases.extend(banking_fuzz_cases(campaign=campaign, changed_files=changed_files, symbols=symbols, seed=seed))
        elif surface == "instruction_trace":
            cases.extend(dynamic_taint_handoff_cases(campaign=campaign, seed=seed))
        else:
            cases.extend(dynamic_or_planning_cases(campaign=campaign, symbols=symbols, symptom=symptom, seed=seed))
    return cases[:max_cases]


def generation_counterexample_cases(*, campaign: dict[str, Any], seed: int) -> list[dict[str, Any]]:
    source = str(campaign.get("counterexample_source", "generation"))
    proof_level = str(campaign.get("proof_level", "planning"))
    case = fuzz_case(
        campaign=campaign,
        seed=seed,
        case_index=0,
        fuzz_type="dynamic_counterexample" if is_dynamic_proof_level(proof_level) else "planning_probe",
        changed_file="",
        expectations=[f"counterexample_source={source}"],
        commands=list(campaign.get("commands", [])),
        proof_level=proof_level,
        notes=[
            "Run these counterexample commands in order; setup/materialization commands may produce inputs for later trace or replay commands.",
            *string_items(campaign.get("counterexample_reasons")),
        ],
    )
    case["counterexample_source"] = source
    case["related_symbols"] = string_items(campaign.get("related_symbols"))
    case["related_addresses"] = string_items(campaign.get("related_addresses"))
    return [case]


def content_fuzz_cases(
    *,
    campaign: dict[str, Any],
    changed_files: tuple[str, ...],
    max_cases: int,
    seed: int,
    scenario_manifest_path: str,
    root: Path,
) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    scenarios = attach_behavioral_probes(
        scenarios=content_scenario_records(
            changed_files=changed_files,
            max_cases=max_cases,
            seed=seed,
            root=root,
        ),
        scenario_manifest_path=scenario_manifest_path,
    )
    for scenario_index, scenario in enumerate(scenarios):
        runtime_targets = scenario.get("runtime_targets") if isinstance(scenario.get("runtime_targets"), dict) else {}
        behavioral_probes = [
            probe
            for probe in scenario.get("behavioral_probes", [])
            if isinstance(probe, dict)
        ]
        case = fuzz_case(
            campaign=campaign,
            seed=seed,
            case_index=scenario_index,
            fuzz_type=str(scenario.get("scenario_type", "content_scenario")),
            changed_file=str(scenario.get("source_file", "")),
            expectations=string_items(scenario.get("expected")),
            commands=[
                *string_items(scenario.get("commands")),
                *[
                    str(probe.get("command", ""))
                    for probe in scenario.get("behavioral_probes", [])
                    if isinstance(probe, dict)
                ],
            ],
            proof_level=str(scenario.get("proof_level", "semantic_source")),
            notes=[
                f"scenario_id={scenario.get('id', '')}",
                *string_items(scenario.get("known_limits")),
            ],
        )
        case["scenario_id"] = str(scenario.get("id", ""))
        case["scenario_type"] = str(scenario.get("scenario_type", ""))
        case["source_file"] = str(scenario.get("source_file", ""))
        case["trigger"] = scenario.get("trigger", {})
        case["state_preconditions"] = scenario.get("state_preconditions", [])
        case["runtime_targets"] = runtime_targets
        case["runtime_route"] = str(runtime_targets.get("runtime_route", ""))
        case["related_symbols"] = string_items(scenario.get("related_symbols"))
        case["outputs"] = scenario.get("outputs", [])
        case["behavioral_probes"] = behavioral_probes
        case["behavioral_probe_count"] = len(behavioral_probes)
        if scenario.get("state_preconditions"):
            case["proof_level"] = "positioned_state_dynamic_planned"
            case["materialization_request"] = content_materialization_request(
                scenario,
                scenario_manifest_path=scenario_manifest_path,
            )
        cases.append(case)
    for file_index, raw_path in enumerate(changed_files):
        path = resolve_path(raw_path, root=root)
        normalized = normalize_path(raw_path)
        if not path.exists() or path.is_dir():
            cases.append(
                fuzz_case(
                    campaign=campaign,
                    seed=seed,
                    case_index=10_000 + file_index,
                    fuzz_type="source_exists",
                    changed_file=normalized,
                    expectations=[],
                    commands=[
                        f"python -m tools.debugger ingest --changed-file {normalized}",
                        f"python -m tools.debugger expect --source-file {normalized} --expect report-valid",
                    ],
                    proof_level="static_expectation",
                    notes=[f"source path was not readable when the fuzz plan was built: {normalized}"],
                )
            )
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        probes = infer_source_expectations(text, normalized)
        if not probes:
            probes = [{"kind": "contains", "value": first_label(text) or ""}]
        for probe_index, probe in enumerate(probes[:8]):
            value = str(probe.get("value", ""))
            expectations = [f"{probe['kind']}={value}"] if value else []
            commands = [
                f"python -m tools.debugger expect --source-file {normalized} --expect {probe['kind']}={value}"
            ] if value else [
                f"python -m tools.debugger expect --source-file {normalized} --expect report-valid"
            ]
            commands.extend(
                [
                    f"python -m tools.debugger content-mirror --source-file {normalized}",
                    f"python -m tools.debugger provenance --source-file {normalized}",
                    f"python -m tools.debugger compare --changed-file {normalized}",
                ]
            )
            cases.append(
                fuzz_case(
                    campaign=campaign,
                    seed=seed,
                    case_index=10_000 + file_index * 100 + probe_index,
                    fuzz_type=f"source_{probe['kind']}",
                    changed_file=normalized,
                    expectations=expectations,
                    commands=commands,
                    proof_level="static_expectation",
                    notes=[str(probe.get("reason", ""))],
                )
            )
    return cases


def banking_fuzz_cases(
    *,
    campaign: dict[str, Any],
    changed_files: tuple[str, ...],
    symbols: tuple[str, ...],
    seed: int,
) -> list[dict[str, Any]]:
    source_file = normalize_path(changed_files[0]) if changed_files else ""
    cases = []
    target_symbols = unique_list([*symbols, *BANKING_WATCH_SYMBOLS, *BANKING_TRACE_SYMBOLS])
    for index in range(8):
        profile_id, patches = banking_patch_profile(index)
        request = banking_state_space_request(
            profile_id=profile_id,
            patches=patches,
            report_stem=f".local\\tmp\\debugger_banking_fuzz_{seed}_{index:04d}",
            source_file=source_file,
        )
        commands = [
            f"python -m tools.debugger provenance --symbol {target_symbols[index % len(target_symbols)]}",
            *request["commands"],
            "python tools\\audit\\check_farcall_a_clobber.py",
            "python tools\\audit\\check_farcall_hl_clobber.py",
            "python tools\\audit\\check_cross_bank_call.py",
        ]
        case = fuzz_case(
            campaign=campaign,
            seed=seed,
            case_index=index,
            fuzz_type="banking_state_probe",
            changed_file=source_file,
            expectations=banking_patch_expectations(patches),
            commands=commands,
            proof_level="dynamic_state_probe_planned",
            notes=[
                f"profile_id={profile_id}",
                "Materialize a patched banking save state, replay bank-shadow writes, trace FarCall/Bankswitch, then run dynamic taint on watched bank state.",
            ],
        )
        case["profile_id"] = profile_id
        case["state_space_request"] = request
        case["watch_symbols"] = list(BANKING_WATCH_SYMBOLS)
        case["trace_symbols"] = list(BANKING_TRACE_SYMBOLS)
        case["related_symbols"] = target_symbols
        cases.append(case)
    return cases


def dynamic_taint_handoff_cases(*, campaign: dict[str, Any], seed: int) -> list[dict[str, Any]]:
    source_report = str(campaign.get("source_report", ""))
    case = fuzz_case(
        campaign=campaign,
        seed=seed,
        case_index=0,
        fuzz_type="dynamic_taint_handoff",
        changed_file="",
        expectations=[f"source_report={source_report}"] if source_report else [],
        commands=list(campaign.get("commands", [])),
        proof_level="dynamic_trace",
        notes=[
            "Run dynamic taint from a validated instruction trace report.",
            f"trace_count={campaign.get('trace_count', 0)}",
        ],
    )
    case["source_report"] = source_report
    case["trace_count"] = int(campaign.get("trace_count", 0))
    case["traces"] = list(campaign.get("traces", []))
    case["sink_symbols"] = list(campaign.get("sink_symbols", []))
    case["sink_addresses"] = list(campaign.get("sink_addresses", []))
    case["source_regs"] = list(campaign.get("source_regs", []))
    case["source_mems"] = list(campaign.get("source_mems", []))
    case["source_symbols"] = list(campaign.get("source_symbols", []))
    return [case]


def dynamic_or_planning_cases(
    *,
    campaign: dict[str, Any],
    symbols: tuple[str, ...],
    symptom: str,
    seed: int,
) -> list[dict[str, Any]]:
    commands = list(campaign.get("commands", []))[:6]
    targets = list(symbols) or [str(campaign.get("surface", "general"))]
    cases = []
    for index, target in enumerate(targets[:8]):
        cases.append(
            fuzz_case(
                campaign=campaign,
                seed=seed,
                case_index=index,
                fuzz_type="dynamic_counterexample" if is_dynamic_proof_level(campaign.get("proof_level")) else "planning_probe",
                changed_file="",
                expectations=[f"symbol={target}"] if target and target != "general" else [],
                commands=commands,
                proof_level=str(campaign.get("proof_level", "planning")),
                notes=[symptom] if symptom else [],
            )
        )
    return cases


def infer_source_expectations(text: str, path: str) -> list[dict[str, str]]:
    probes: list[dict[str, str]] = []
    for macro in CONTENT_MACROS:
        if macro in text:
            probes.append(
                {
                    "kind": "contains",
                    "value": macro,
                    "reason": f"{path} already uses {macro}; keep this source invariant visible.",
                }
            )
    label = first_label(text)
    if label:
        probes.insert(
            0,
            {
                "kind": "contains",
                "value": label,
                "reason": "Keep the primary label present in source-level fuzz probes.",
            },
        )
    probes.append(
        {
            "kind": "not-contains",
            "value": "__DEBUGGER_FORBIDDEN_SENTINEL__",
            "reason": "Negative sentinel verifies source expectation plumbing.",
        }
    )
    return unique_probes(probes)


def first_label(text: str) -> str:
    for line in text.splitlines():
        match = LABEL_RE.match(line)
        if match:
            return match.group(1)
    return ""


def is_dynamic_proof_level(value: Any) -> bool:
    text = str(value)
    return text == "dynamic" or text.startswith("dynamic_") or text.startswith("positioned_state_dynamic")


def content_materialization_request(scenario: dict[str, Any], *, scenario_manifest_path: str) -> dict[str, Any]:
    scenario_id = str(scenario.get("id", ""))
    state_report = f".local\\tmp\\debugger_content_state_{scenario_id}.json"
    state_path = f".local\\tmp\\debugger_content_state_{scenario_id}.state"
    return {
        "kind": "content_positioned_state",
        "scenario_id": scenario_id,
        "scenario_manifest": scenario_manifest_path,
        "out_state": state_path,
        "out_report": state_report,
        "precondition_count": len(scenario.get("state_preconditions", [])),
        "commands": [
            (
                "python -m tools.debugger content-state "
                f"--scenario {scenario_manifest_path} --scenario-id {scenario_id} "
                f"--json-out {state_report}"
            ),
            (
                "python -m tools.debugger content-state "
                f"--scenario {scenario_manifest_path} --scenario-id {scenario_id} "
                f"--base-save-state <base_state> --out-state {state_path} "
                f"--execute --json-out {state_report}"
            ),
            (
                "python -m tools.debugger replay "
                f"--report {state_report} --scenario {scenario_manifest_path} "
                f"--scenario-id {scenario_id} --execute-watch"
            ),
            content_state_instruction_trace_command(
                state_report=state_report,
                scenario_id=scenario_id,
            ),
        ],
    }


def content_probe_commands(*, changed_files: tuple[str, ...], root: Path) -> list[str]:
    commands = []
    for raw_path in changed_files[:6]:
        normalized = normalize_path(raw_path)
        path = resolve_path(raw_path, root=root)
        commands.append(f"python -m tools.debugger ingest --changed-file {normalized}")
        commands.append(f"python -m tools.debugger content-mirror --source-file {normalized}")
        commands.append(
            f"python -m tools.debugger content-scenarios --source-file {normalized} --out-scenarios .local\\tmp\\debugger_content_scenarios.jsonl"
        )
        commands.append(f"python -m tools.debugger expect --source-file {normalized} --expect report-valid")
        if path.exists() and path.is_file():
            probes = infer_source_expectations(path.read_text(encoding="utf-8", errors="replace"), normalized)
            for probe in probes[:2]:
                commands.append(
                    f"python -m tools.debugger expect --source-file {normalized} --expect {probe['kind']}={probe['value']}"
                )
    return unique_list(commands)


def fuzz_case(
    *,
    campaign: dict[str, Any],
    seed: int,
    case_index: int,
    fuzz_type: str,
    changed_file: str,
    expectations: list[str],
    commands: list[str],
    proof_level: str,
    notes: list[str],
) -> dict[str, Any]:
    surface = str(campaign.get("surface", "general"))
    campaign_slug = slug_id(str(campaign.get("id", "")) or surface)
    return {
        "id": f"debugger_fuzz_{campaign_slug}_{seed}_{case_index:04d}",
        "kind": "unified_debugger_fuzz_case",
        "campaign_id": campaign.get("id", ""),
        "surface": surface,
        "proof_level": proof_level,
        "fuzz_type": fuzz_type,
        "seed": seed,
        "case_index": case_index,
        "changed_file": changed_file,
        "symbols": list(campaign.get("symbols", [])),
        "related_symbols": string_items(campaign.get("related_symbols")),
        "related_addresses": string_items(campaign.get("related_addresses")),
        "expectations": expectations,
        "commands": unique_list(commands),
        "notes": [note for note in notes if note],
        "status": "planned",
    }


def write_case_records(
    *,
    records: list[dict[str, Any]],
    out_cases: str,
    root: Path,
) -> dict[str, Any]:
    if not out_cases:
        return {"path": "", "written": False, "record_count": len(records), "errors": []}
    path = resolve_path(out_cases, root=root)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
            encoding="utf-8",
            newline="\n",
        )
    except OSError as exc:
        return {
            "path": display_path(path, root=root),
            "written": False,
            "record_count": 0,
            "errors": [str(exc)],
        }
    return {
        "path": display_path(path, root=root),
        "written": True,
        "record_count": len(records),
        "errors": [],
    }


def fuzz_title(generator: dict[str, Any]) -> str:
    title = str(generator.get("title", "")).strip()
    return title if title else f"{generator.get('surface', 'general')} fuzz campaign"


def command_strings(value: Any) -> list[str]:
    commands = []
    for item in dict_items(value):
        commands.extend(string_items(item.get("command")))
    commands.extend(item for item in string_items(value) if item.startswith("python "))
    return unique_list(commands)


def unique_probes(probes: list[dict[str, str]]) -> list[dict[str, str]]:
    out = []
    seen: set[tuple[str, str]] = set()
    for probe in probes:
        key = (probe["kind"], probe["value"])
        if not probe["value"] or key in seen:
            continue
        seen.add(key)
        out.append(probe)
    return out


def dict_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [item for item in value if isinstance(item, dict)]


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


def slug_id(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "counterexample"
