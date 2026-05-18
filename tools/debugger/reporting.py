from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from .catalog import ROOT
from .ranking import display_path, proof_status_counts, rank_findings, resolve_path, with_proof_status


REPORT_FORMATS = {"markdown", "html"}
SUMMARY_KEYS = (
    "ready",
    "valid",
    "executed",
    "passed",
    "status_counts",
    "artifact_count",
    "packet_id",
    "error_count",
    "warning_count",
    "blocking_gap_count",
    "match_count",
    "expectation_count",
    "passed_count",
    "step_count",
    "failed_count",
    "skipped_count",
    "hit_count",
    "context_frames",
    "dynamic_context_event_count",
    "finding_count",
    "proof_status_counts",
    "impact_count",
    "phase_count",
    "investigation_step_count",
    "produced_report_count",
    "command_count",
    "watch_symbol_count",
    "symbol_count",
    "source_file_count",
    "source_artifact_count",
    "evidence_scenario_count",
    "evidence_state_precondition_count",
    "evidence_state_patch_count",
    "invariant_count",
    "passed_invariant_count",
    "failed_invariant_count",
    "warning_invariant_count",
    "rom_mirror_count",
    "passed_rom_mirror_count",
    "failed_rom_mirror_count",
    "warning_rom_mirror_count",
    "scenario_id_count",
    "behavioral_probe_count",
    "runtime_probe_count",
    "content_scenario_count",
    "dynamic_event_count",
    "trace_observation_count",
    "effect_event_count",
    "memory_read_count",
    "memory_write_count",
    "stack_read_count",
    "stack_write_count",
    "io_read_count",
    "io_write_count",
    "watch_read_count",
    "watch_write_count",
    "all_event_count",
    "matched_event_count",
    "write_event_count",
    "read_event_count",
    "flow_event_count",
    "causal_link_count",
    "reverse_attribution_count",
    "write_attribution_count",
    "trace_synthesis_route_count",
    "trace_synthesis_executed",
    "sink_count",
    "contributor_count",
    "target_symbol_count",
    "target_file_count",
    "node_count",
    "edge_count",
    "path_count",
    "timeline_event_count",
    "waterfall_step_count",
    "graph_node_count",
    "graph_edge_count",
    "target_count",
    "result_count",
    "covered_target_count",
    "indirect_target_count",
    "uncovered_target_count",
    "coverage_ratio",
    "covered_address_count",
    "scenario_count",
    "selected_scenario_count",
    "surface_count",
    "generator_count",
    "campaign_count",
    "dynamic_campaign_count",
    "static_campaign_count",
    "fuzz_case_count",
    "counterexample_count",
    "materialization_step_count",
    "materialization_count",
    "patch_count",
    "seed_count",
)


def build_static_report(
    *,
    reports: tuple[str, ...],
    output_format: str = "markdown",
    title: str = "Unified Pokemon Gold Romhack Debugger Report",
    root: Path = ROOT,
) -> dict[str, Any]:
    if output_format not in REPORT_FORMATS:
        raise ValueError(f"unknown report format: {output_format}")

    loaded_reports, load_errors = load_reports(reports=reports, root=root)
    findings, ranking_errors = collect_ranked_findings(
        reports=reports,
        loaded_reports=loaded_reports,
        root=root,
    )
    summaries = [summarize_input_report(item["source"], item["data"]) for item in loaded_reports]
    errors = unique_list([*load_errors, *ranking_errors])
    content = render_markdown_report(
        title=title,
        root=root,
        requested_count=len(reports),
        summaries=summaries,
        findings=findings,
        errors=errors,
    )
    if output_format == "html":
        content = render_html_report(
            title=title,
            root=root,
            requested_count=len(reports),
            summaries=summaries,
            findings=findings,
            errors=errors,
        )

    return {
        "schema_version": 1,
        "kind": "unified_debugger_static_report",
        "root": str(root),
        "valid": not load_errors and not ranking_errors,
        "format": output_format,
        "title": title,
        "requested_report_count": len(reports),
        "loaded_report_count": len(loaded_reports),
        "finding_count": len(findings),
        "proof_status_counts": proof_status_counts(findings),
        "error_count": len(errors),
        "errors": errors,
        "sources": [summary["source"] for summary in summaries],
        "content": content,
    }


def load_reports(
    *,
    reports: tuple[str, ...],
    root: Path,
) -> tuple[list[dict[str, Any]], list[str]]:
    loaded: list[dict[str, Any]] = []
    errors: list[str] = []
    for report_path in reports:
        path = resolve_path(report_path, root=root)
        source = display_path(path, root=root)
        if not path.exists():
            errors.append(f"missing report: {report_path}")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{report_path}: invalid JSON: {exc.msg}")
            continue
        loaded.append({"path": path, "source": source, "data": data})
    return loaded, errors


def collect_ranked_findings(
    *,
    reports: tuple[str, ...],
    loaded_reports: list[dict[str, Any]],
    root: Path,
) -> tuple[list[dict[str, Any]], list[str]]:
    findings: list[dict[str, Any]] = []
    ranking_inputs: list[str] = []
    loaded_by_source = {item["source"]: item["data"] for item in loaded_reports}

    for report_path in reports:
        path = resolve_path(report_path, root=root)
        source = display_path(path, root=root)
        data = loaded_by_source.get(source)
        if not data:
            continue
        if data.get("kind") == "unified_debugger_ranked_findings":
            findings.extend(with_proof_status(item) for item in dict_items(data.get("findings")))
        else:
            ranking_inputs.append(report_path)

    errors: list[str] = []
    if ranking_inputs:
        ranked = rank_findings(reports=tuple(ranking_inputs), root=root)
        findings.extend(ranked.get("findings", []))
        errors.extend(ranked.get("errors", []))

    findings.sort(
        key=lambda item: (
            -int(item.get("severity", 0)),
            -float(item.get("confidence", 0.0)),
            str(item.get("source", "")),
            str(item.get("title", "")),
        )
    )
    return findings, errors


def summarize_input_report(source: str, report: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": source,
        "kind": str(report.get("kind", "<missing-kind>")),
        "summary": summarize_status(report),
        "commands": collect_commands(report, source=source),
        "gaps": collect_gaps(report),
        "issues": collect_issues(report),
        "candidates": collect_candidates(report),
    }


def summarize_status(report: dict[str, Any]) -> list[str]:
    summary: list[str] = []
    for key in SUMMARY_KEYS:
        if key not in report:
            continue
        value = report[key]
        if isinstance(value, dict):
            value = ", ".join(f"{name}={count}" for name, count in sorted(value.items()))
        summary.append(f"{key}={value}")
    return summary


def format_counts(counts: dict[str, int]) -> str:
    return ", ".join(f"{name}={count}" for name, count in sorted(counts.items()) if count)


def collect_commands(report: dict[str, Any], *, source: str = "") -> list[str]:
    commands: list[str] = []
    state_patch_minimization = report.get("state_patch_minimization")
    if isinstance(state_patch_minimization, dict) and source:
        add_strings(commands, f"python -m tools.debugger provenance --report {source}")
        add_strings(commands, f"python -m tools.debugger taint --report {source}")
        add_strings(commands, f"python -m tools.debugger slice --report {source}")
    add_strings(commands, report.get("commands"))
    add_strings(commands, report.get("materialization_commands"))
    add_strings(commands, report.get("counterexample_commands"))
    for step in dict_items(report.get("steps")):
        add_strings(commands, step.get("command"))
        add_strings(commands, step.get("commands"))
    for step in dict_items(report.get("materialization_steps")):
        add_strings(commands, step.get("command"))
    evidence_minimization = report.get("evidence_minimization")
    if isinstance(evidence_minimization, dict) and evidence_minimization.get("out_trace"):
        add_strings(commands, f"python -m tools.debugger trace-index --trace {evidence_minimization['out_trace']}")
    if isinstance(state_patch_minimization, dict):
        add_strings(commands, state_patch_minimization.get("commands"))
    trace_synthesis_plan = report.get("trace_synthesis_plan")
    if isinstance(trace_synthesis_plan, dict):
        add_strings(commands, trace_synthesis_plan.get("commands"))
        for route in dict_items(trace_synthesis_plan.get("routes")):
            add_strings(commands, route.get("commands"))
    for counterexample in dict_items(report.get("counterexamples")):
        add_strings(commands, counterexample.get("command"))
    for expectation in dict_items(report.get("expectations")):
        add_strings(commands, expectation.get("commands"))
    for invariant in dict_items(report.get("invariants")):
        add_strings(commands, invariant.get("commands"))
    for scenario in dict_items(report.get("scenarios")):
        add_strings(commands, scenario.get("commands"))
        for probe in dict_items(scenario.get("behavioral_probes")):
            add_strings(commands, probe.get("command"))
    for case in dict_items(report.get("fuzz_cases")):
        add_strings(commands, case.get("commands"))
        materialization_request = case.get("materialization_request")
        if isinstance(materialization_request, dict):
            add_strings(commands, materialization_request.get("commands"))
        for probe in dict_items(case.get("behavioral_probes")):
            add_strings(commands, probe.get("command"))
    for campaign in dict_items(report.get("campaigns")):
        add_strings(commands, campaign.get("commands"))
    for event in dict_items(report.get("events")):
        add_strings(commands, event.get("commands"))
    for path in dict_items(report.get("causal_paths")):
        add_strings(commands, path.get("commands"))
    for path in dict_items(report.get("paths")):
        add_strings(commands, path.get("commands"))
    for attribution in dict_items(report.get("write_attributions")):
        add_strings(commands, attribution.get("commands"))
    for item in dict_items(report.get("reverse_attributions")):
        add_strings(commands, item.get("commands"))
    for generator in dict_items(report.get("generators")):
        for key in ("commands", "counterexample_commands", "materialization_commands"):
            for item in dict_items(generator.get(key)):
                add_strings(commands, item.get("command"))
    for match in dict_items(report.get("matches")):
        add_strings(commands, match.get("commands"))
        add_strings(commands, match.get("materialization_commands"))
        add_strings(commands, match.get("counterexample_commands"))
    for capability in dict_items(report.get("capabilities")):
        add_strings(commands, capability.get("commands"))
    for symbol in dict_items(report.get("symbols")):
        add_strings(commands, symbol.get("suggested_commands"))
    for watch in dict_items(report.get("watches")):
        add_strings(commands, watch.get("suggested_commands"))
    for target in dict_items(report.get("targets")):
        add_strings(commands, target.get("suggested_commands"))
    for item in dict_items(report.get("items")):
        add_strings(commands, item.get("next_actions"))
    for path in dict_items(report.get("paths")):
        add_strings(commands, path.get("commands"))
    for event in dict_items(report.get("timeline")):
        add_strings(commands, event.get("commands"))
    for phase in dict_items(report.get("phase_steps")):
        for step in dict_items(phase.get("steps")):
            add_strings(commands, step.get("command"))
    for source in dict_items(report.get("source_files")):
        add_strings(commands, source.get("suggested_commands"))
    return unique_list(commands)[:16]


def collect_gaps(report: dict[str, Any]) -> list[str]:
    gaps: list[str] = []
    add_strings(gaps, report.get("blocking_gaps"))
    for capability in dict_items(report.get("capabilities")):
        add_strings(gaps, capability.get("gaps"))
    for match in dict_items(report.get("matches")):
        add_strings(gaps, match.get("gaps"))
    for generator in dict_items(report.get("generators")):
        add_strings(gaps, generator.get("gaps"))
    for campaign in dict_items(report.get("campaigns")):
        add_strings(gaps, campaign.get("gaps"))
    add_strings(gaps, report.get("known_limits"))
    for target in dict_items(report.get("uncovered_targets")):
        add_strings(gaps, f"uncovered {target.get('type', 'target')}: {target.get('id', '<unknown>')}")
    return unique_list(gaps)[:16]


def collect_issues(report: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    add_strings(issues, report.get("errors"))
    add_strings(issues, report.get("warnings"))
    for artifact in dict_items(report.get("artifacts")):
        add_strings(issues, artifact.get("errors"))
        add_strings(issues, artifact.get("warnings"))
    for step in dict_items(report.get("steps")):
        if step.get("status") == "failed":
            failed_label = step.get("command") or step.get("title") or step.get("id") or "<unknown-step>"
            add_strings(issues, f"failed: {failed_label}")
            add_strings(issues, step.get("errors"))
            add_strings(issues, step.get("warnings"))
            add_strings(issues, step.get("stderr_tail"))
            add_strings(issues, step.get("stdout_tail"))
    for symbol in dict_items(report.get("symbols")):
        add_strings(issues, symbol.get("warnings"))
    for target in dict_items(report.get("targets")):
        add_strings(issues, target.get("warnings"))
    for source in dict_items(report.get("source_files")):
        add_strings(issues, source.get("errors"))
    for expectation in dict_items(report.get("expectations")):
        if expectation.get("status") == "failed":
            add_strings(issues, f"failed expectation: {expectation.get('id', '<unknown>')}")
            add_strings(issues, expectation.get("evidence"))
    for invariant in dict_items(report.get("invariants")):
        if invariant.get("status") in {"failed", "warning"}:
            add_strings(issues, f"{invariant.get('status')} content invariant: {invariant.get('id', '<unknown>')}")
            add_strings(issues, invariant.get("evidence"))
    validation = report.get("execution_validation") if isinstance(report.get("execution_validation"), dict) else {}
    if validation.get("attempted"):
        if not validation.get("hit"):
            add_strings(issues, "instruction trace hooks did not fire")
        if validation.get("missing_function_symbols"):
            add_strings(issues, "instruction trace missed functions: " + ", ".join(string_items(validation.get("missing_function_symbols"))[:8]))
        if validation.get("trace_record_limit_hit"):
            add_strings(issues, "instruction trace reached record limit")
    trace_synthesis_plan = report.get("trace_synthesis_plan")
    if isinstance(trace_synthesis_plan, dict):
        for route in dict_items(trace_synthesis_plan.get("routes")):
            status = str(route.get("state_status", ""))
            if status.startswith("requires"):
                add_strings(
                    issues,
                    f"trace synthesis requires setup: {route.get('match_id') or route.get('id') or status}",
                )
    return unique_list(issues)[:16]


def collect_candidates(report: dict[str, Any]) -> list[str]:
    candidates = []
    for candidate in dict_items(report.get("candidates"))[:10]:
        candidates.append(
            f"S{candidate.get('score', 0)} {candidate.get('type', 'candidate')}: {candidate.get('id', '<unknown>')}"
        )
    for target in dict_items(report.get("targets"))[:10]:
        candidates.append(
            f"{target.get('status', 'unknown')} {target.get('type', 'target')}: {target.get('id', '<unknown>')}"
        )
    for item in dict_items(report.get("items"))[:10]:
        candidates.append(
            f"I{item.get('impact_score', 0)} {item.get('type', 'impact')}: {item.get('title', '<unknown>')}"
            f"{address_suffix(item)}{semantic_suffix(item)}"
        )
    for item in dict_items(report.get("top_impact"))[:10]:
        candidates.append(
            f"I{item.get('impact_score', 0)} {item.get('type', 'impact')}: {item.get('title', '<unknown>')}"
            f"{address_suffix(item)}{semantic_suffix(item)}"
        )
    for finding in dict_items(report.get("top_findings"))[:10]:
        candidates.append(
            f"S{finding.get('severity', 0)} {finding.get('type', 'finding')}: {finding.get('title', '<unknown>')}"
            f"{address_suffix(finding)}"
        )
    for produced in dict_items(report.get("reports"))[:10]:
        candidates.append(
            f"{produced.get('id', '<unknown>')} {produced.get('kind', '<unknown-kind>')}: {produced.get('path', '')}"
        )
    for generator in dict_items(report.get("generators"))[:10]:
        candidates.append(
            f"{generator.get('status', 'unknown')} generator: {generator.get('id', '<unknown>')}"
        )
    for campaign in dict_items(report.get("campaigns"))[:10]:
        sinks = ", ".join(
            [
                *string_items(campaign.get("related_symbols"))[:4],
                *string_items(campaign.get("related_addresses"))[:4],
            ]
        )
        candidates.append(
            f"{campaign.get('proof_level', 'planned')} fuzz campaign: "
            f"{campaign.get('id', '<unknown>')}"
            f"{' sinks=' + sinks if sinks else ''}"
        )
    for scenario in dict_items(report.get("scenarios"))[:10]:
        if scenario.get("kind") == "unified_debugger_content_scenario" or scenario.get("scenario_type"):
            candidates.append(
                f"{scenario.get('proof_level', 'scenario')} scenario: "
                f"{scenario.get('id', '<unknown>')} {scenario.get('scenario_type', '')}".strip()
            )
            runtime_targets = scenario.get("runtime_targets") if isinstance(scenario.get("runtime_targets"), dict) else {}
            for symbol in string_items(runtime_targets.get("trace_symbols"))[:4]:
                candidates.append(f"runtime helper: {symbol}")
            for symbol in string_items(runtime_targets.get("watch_symbols"))[:4]:
                candidates.append(f"runtime watch: {symbol}")
    for case in dict_items(report.get("fuzz_cases"))[:10]:
        candidates.append(
            f"{case.get('proof_level', 'fuzz')} fuzz case: "
            f"{case.get('id', '<unknown>')} {case.get('fuzz_type', '')}".strip()
        )
        runtime_targets = case.get("runtime_targets") if isinstance(case.get("runtime_targets"), dict) else {}
        for symbol in string_items(runtime_targets.get("trace_symbols"))[:4]:
            candidates.append(f"fuzz runtime helper: {symbol}")
        for symbol in string_items(runtime_targets.get("watch_symbols"))[:4]:
            candidates.append(f"fuzz runtime watch: {symbol}")
    scenario_manifest = report.get("scenario_manifest")
    if isinstance(scenario_manifest, dict) and scenario_manifest.get("path"):
        state = "written" if scenario_manifest.get("written") else "planned"
        candidates.append(
            f"{state} scenarios: {scenario_manifest.get('path')} ({scenario_manifest.get('record_count', 0)})"
        )
    seed_manifest = report.get("seed_manifest")
    if isinstance(seed_manifest, dict) and seed_manifest.get("path"):
        state = "written" if seed_manifest.get("written") else "planned"
        candidates.append(
            f"{state} seeds: {seed_manifest.get('path')} ({seed_manifest.get('record_count', 0)})"
        )
    evidence_minimization = report.get("evidence_minimization")
    if isinstance(evidence_minimization, dict) and evidence_minimization.get("attempted"):
        state = "preserved" if evidence_minimization.get("preserved") else "failed"
        candidates.append(
            f"{state} evidence minimization: {evidence_minimization.get('original_count', 0)} -> {evidence_minimization.get('minimized_count', 0)} records; context {evidence_minimization.get('context_frame_original_count', 0)} -> {evidence_minimization.get('context_frame_minimized_count', 0)}"
        )
    state_patch_minimization = report.get("state_patch_minimization")
    if isinstance(state_patch_minimization, dict) and state_patch_minimization.get("attempted"):
        state = "preserved" if state_patch_minimization.get("preserved") else "failed"
        watch_addresses = ", ".join(string_items(state_patch_minimization.get("watch_addresses"))[:4])
        source_mems = ", ".join(string_items(state_patch_minimization.get("source_mems"))[:4])
        reducer_surfaces = ", ".join(string_items(state_patch_minimization.get("semantic_reducer_surfaces"))[:6])
        candidates.append(
            f"{state} state-space patch minimization: {state_patch_minimization.get('original_patch_count', 0)} -> {state_patch_minimization.get('minimized_patch_count', 0)} patches"
            f"{'; watch_addresses=' + watch_addresses if watch_addresses else ''}"
            f"{'; source_mems=' + source_mems if source_mems else ''}"
            f"; semantic_watch={state_patch_minimization.get('semantic_watch_rerun_count', 0)}/{state_patch_minimization.get('semantic_watch_rerun_attempt_count', 0)}"
            f"; semantic_replay={state_patch_minimization.get('semantic_replay_rerun_count', 0)}/{state_patch_minimization.get('semantic_replay_rerun_attempt_count', 0)}"
            f"{'; semantic_reducers=' + reducer_surfaces if reducer_surfaces else ''}"
        )
        for route in dict_items(state_patch_minimization.get("semantic_reducer_routes"))[:8]:
            commands = string_items(route.get("commands"))
            candidates.append(
                "semantic reducer route: "
                f"{route.get('surface', 'general')} {route.get('id', '<unknown>')}"
                f"{' source=' + route.get('source_file', '') if route.get('source_file') else ''}"
                f" commands={len(commands)}"
            )
    trace_synthesis_plan = report.get("trace_synthesis_plan")
    if isinstance(trace_synthesis_plan, dict):
        for route in dict_items(trace_synthesis_plan.get("routes"))[:10]:
            route_id = route.get("match_id") or route.get("id") or route.get("source_kind") or "route"
            sinks = ", ".join(string_items(route.get("sink_symbols"))[:4] + string_items(route.get("sink_addresses"))[:4])
            sources = ", ".join(trace_synthesis_related_sources(route)[:4])
            source_mems = ", ".join(string_items(route.get("source_mems"))[:4])
            candidates.append(
                "trace synthesis: "
                f"{route.get('state_status', 'planned')} {route_id}"
                f"{' -> ' + route.get('trace_output', '') if route.get('trace_output') else ''}"
                f"{' sources=' + sources if sources else ''}"
                f"{' source_mems=' + source_mems if source_mems else ''}"
                f"{' sinks=' + sinks if sinks else ''}"
            )
    for expectation in dict_items(report.get("expectations"))[:10]:
        candidates.append(
            f"{expectation.get('status', 'unknown')} expectation: {expectation.get('id', '<unknown>')}"
        )
    for invariant in dict_items(report.get("invariants"))[:10]:
        candidates.append(
            f"{invariant.get('status', 'unknown')} invariant: {invariant.get('id', '<unknown>')}"
        )
    replay_targets = report.get("replay_targets")
    if isinstance(replay_targets, dict):
        for symbol in replay_targets.get("watch_symbols", [])[:10]:
            candidates.append(f"watch target: {symbol}")
        for symbol in replay_targets.get("symbols", [])[:10]:
            candidates.append(f"symbol target: {symbol}")
        for path in replay_targets.get("source_files", [])[:10]:
            candidates.append(f"source target: {path}")
    for path in dict_items(report.get("paths"))[:10]:
        candidates.append(
            f"S{path.get('score', 0)} causal path: {path.get('title', '<unknown>')}"
        )
    for path in dict_items(report.get("causal_paths"))[:10]:
        candidates.append(
            f"S{path.get('score', 0)} trace path: {path.get('title', '<unknown>')}"
        )
    for item in dict_items(report.get("reverse_attributions"))[:10]:
        candidates.append(
            f"C{item.get('confidence', 0)} reverse attribution: {item.get('title', '<unknown>')}"
        )
    for item in dict_items(report.get("write_attributions"))[:10]:
        candidates.append(
            f"C{item.get('confidence', 0)} dynamic write: {item.get('target', '<sink>')} at {item.get('pc_label', '<pc>')}"
            f"{address_suffix(item)}"
        )
    for event in dict_items(report.get("events"))[:10]:
        state = event.get("state_symbol") or event.get("bank_address") or event.get("address") or "<unknown>"
        candidates.append(
            f"{event.get('event_type', 'event')}: {state}"
        )
    for event in dict_items(report.get("timeline"))[:10]:
        candidates.append(
            f"S{event.get('severity', 0)} {event.get('lane', 'timeline')}: {event.get('title', '<unknown>')}"
        )
    validation = report.get("execution_validation") if isinstance(report.get("execution_validation"), dict) else {}
    if validation:
        trace_path = instruction_trace_output_path(report)
        candidates.append(
            "instruction trace validation: "
            f"hit={validation.get('hit')} "
            f"captured={validation.get('captured_frame_count', report.get('captured_frame_count', 0))} "
            f"ready_for_dynamic_taint={validation.get('ready_for_dynamic_taint')}"
        )
        if validation.get("ready_for_dynamic_taint") and trace_path:
            candidates.append(f"ready dynamic-taint trace: {trace_path}")
        if validation.get("attempted") and not validation.get("hit"):
            missed = ", ".join(string_items(validation.get("missing_function_symbols"))[:6]) or "selected hooks"
            candidates.append(f"missed instruction trace: {missed}")
        for symbol in string_items(validation.get("hit_function_symbols"))[:6]:
            candidates.append(f"instruction hit: {symbol}")
        for symbol in string_items(validation.get("missing_function_symbols"))[:6]:
            candidates.append(f"instruction miss: {symbol}")
        for symbol in string_items(validation.get("watch_symbols"))[:6]:
            candidates.append(f"instruction watch: {symbol}")
    for function in dict_items(report.get("functions"))[:10]:
        symbol = str(function.get("symbol", ""))
        if symbol:
            candidates.append(
                f"trace function: {symbol} instructions={function.get('instruction_count', 0)} hooks={function.get('hook_count', 0)}"
            )
    return candidates


def render_markdown_report(
    *,
    title: str,
    root: Path,
    requested_count: int,
    summaries: list[dict[str, Any]],
    findings: list[dict[str, Any]],
    errors: list[str],
) -> str:
    lines = [
        f"# {title}",
        "",
        "Generated by `python -m tools.debugger report` for this Pokemon Gold romhack worktree.",
        "",
        f"- Root: `{root}`",
        f"- Inputs: {len(summaries)} loaded / {requested_count} requested",
        f"- Normalized findings: {len(findings)}",
        f"- Proof statuses: {format_counts(proof_status_counts(findings)) or 'none'}",
        f"- Input errors: {len(errors)}",
        "",
    ]
    if errors:
        lines.extend(["## Input Errors", ""])
        lines.extend(f"- {truncate(error)}" for error in errors)
        lines.append("")

    lines.extend(["## Highest Priority Findings", ""])
    if findings:
        lines.append("| Severity | Confidence | Proof | Type | Source | Finding |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for finding in findings[:30]:
            proof_status = str(finding.get("proof_status", "planned_only"))
            lines.append(
                "| "
                + " | ".join(
                    (
                        str(finding.get("severity", "")),
                        f"{float(finding.get('confidence', 0.0)):.2f}",
                        markdown_cell(proof_status),
                        markdown_cell(str(finding.get("type", ""))),
                        markdown_cell(str(finding.get("source", ""))),
                        markdown_cell(str(finding.get("title", ""))),
                    )
                )
                + " |"
            )
            addresses = related_addresses(finding)
            if addresses:
                lines.append(
                    "|  |  |  | addresses |  | "
                    f"{markdown_cell(', '.join(f'`{address}`' for address in addresses[:6]))} |"
                )
            for factor in string_items(finding.get("semantic_factors"))[:2]:
                lines.append(f"|  |  |  | semantic |  | {markdown_cell(truncate(str(factor)))} |")
            for evidence in finding.get("evidence", [])[:2]:
                lines.append(f"|  |  |  | evidence |  | {markdown_cell(truncate(str(evidence)))} |")
            for action in finding.get("next_actions", [])[:2]:
                lines.append(f"|  |  |  | next |  | `{markdown_cell(truncate(str(action)))}` |")
    else:
        lines.append("No normalized findings were produced from the input reports.")
    lines.append("")

    lines.extend(["## Input Reports", ""])
    for summary in summaries:
        lines.extend(render_markdown_summary(summary))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_markdown_summary(summary: dict[str, Any]) -> list[str]:
    lines = [
        f"### {summary['source']}",
        "",
        f"- Kind: `{summary['kind']}`",
    ]
    if summary["summary"]:
        lines.append("- Status: " + "; ".join(f"`{item}`" for item in summary["summary"]))
    if summary["commands"]:
        lines.extend(["", "Commands:"])
        lines.extend(f"- `{command}`" for command in summary["commands"])
    if summary["candidates"]:
        lines.extend(["", "Candidates:"])
        lines.extend(f"- {candidate}" for candidate in summary["candidates"])
    if summary["gaps"]:
        lines.extend(["", "Gaps:"])
        lines.extend(f"- {truncate(gap)}" for gap in summary["gaps"])
    if summary["issues"]:
        lines.extend(["", "Issues:"])
        lines.extend(f"- {truncate(issue)}" for issue in summary["issues"])
    return lines


def render_html_report(
    *,
    title: str,
    root: Path,
    requested_count: int,
    summaries: list[dict[str, Any]],
    findings: list[dict[str, Any]],
    errors: list[str],
) -> str:
    rows = []
    for finding in findings[:30]:
        title = escape(str(finding.get("title", "")))
        proof_status = escape(str(finding.get("proof_status", "planned_only")))
        addresses = related_addresses(finding)
        if addresses:
            address_text = ", ".join(f"<code>{escape(address)}</code>" for address in addresses[:6])
            title += f"<br><span class=\"meta\">Addresses: {address_text}</span>"
        semantic = string_items(finding.get("semantic_factors"))
        if semantic:
            semantic_text = "; ".join(escape(item) for item in semantic[:3])
            title += f"<br><span class=\"meta\">Semantic: {semantic_text}</span>"
        rows.append(
            "<tr>"
            f"<td>{escape(str(finding.get('severity', '')))}</td>"
            f"<td>{float(finding.get('confidence', 0.0)):.2f}</td>"
            f"<td>{proof_status}</td>"
            f"<td>{escape(str(finding.get('type', '')))}</td>"
            f"<td>{escape(str(finding.get('source', '')))}</td>"
            f"<td>{title}</td>"
            "</tr>"
        )
    finding_table = "\n".join(rows) or (
        "<tr><td colspan=\"6\">No normalized findings were produced.</td></tr>"
    )
    proof_summary = format_counts(proof_status_counts(findings)) or "none"
    return "\n".join(
        [
            "<!doctype html>",
            "<html lang=\"en\">",
            "<head>",
            "<meta charset=\"utf-8\">",
            f"<title>{escape(title)}</title>",
            "<style>",
            "body{font-family:Segoe UI,Arial,sans-serif;margin:32px;line-height:1.45;color:#1f2328;background:#fff}",
            "h1,h2,h3{line-height:1.2}code{background:#f6f8fa;padding:2px 4px;border-radius:4px}",
            "table{border-collapse:collapse;width:100%;margin:12px 0 24px}th,td{border:1px solid #d0d7de;padding:6px 8px;text-align:left;vertical-align:top}",
            ".meta,.block{margin:0 0 20px}.issue{color:#9a3412}",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>{escape(title)}</h1>",
            "<p>Generated by <code>python -m tools.debugger report</code> for this Pokemon Gold romhack worktree.</p>",
            "<ul class=\"meta\">",
            f"<li>Root: <code>{escape(str(root))}</code></li>",
            f"<li>Inputs: {len(summaries)} loaded / {requested_count} requested</li>",
            f"<li>Normalized findings: {len(findings)}</li>",
            f"<li>Proof statuses: {escape(proof_summary)}</li>",
            f"<li>Input errors: {len(errors)}</li>",
            "</ul>",
            render_html_errors(errors),
            "<h2>Highest Priority Findings</h2>",
            "<table>",
            "<thead><tr><th>Severity</th><th>Confidence</th><th>Proof</th><th>Type</th><th>Source</th><th>Finding</th></tr></thead>",
            f"<tbody>{finding_table}</tbody>",
            "</table>",
            "<h2>Input Reports</h2>",
            "\n".join(render_html_summary(summary) for summary in summaries),
            "</body>",
            "</html>",
            "",
        ]
    )


def render_html_errors(errors: list[str]) -> str:
    if not errors:
        return ""
    items = "".join(f"<li>{escape(truncate(error))}</li>" for error in errors)
    return f"<h2>Input Errors</h2><ul class=\"issue\">{items}</ul>"


def render_html_summary(summary: dict[str, Any]) -> str:
    parts = [
        "<section class=\"block\">",
        f"<h3>{escape(summary['source'])}</h3>",
        f"<p>Kind: <code>{escape(summary['kind'])}</code></p>",
    ]
    if summary["summary"]:
        parts.append(
            "<p>Status: "
            + "; ".join(f"<code>{escape(item)}</code>" for item in summary["summary"])
            + "</p>"
        )
    parts.extend(render_html_list("Commands", summary["commands"], code=True))
    parts.extend(render_html_list("Candidates", summary["candidates"]))
    parts.extend(render_html_list("Gaps", summary["gaps"]))
    parts.extend(render_html_list("Issues", summary["issues"], css_class="issue"))
    parts.append("</section>")
    return "\n".join(parts)


def render_html_list(
    title: str,
    items: list[str],
    *,
    code: bool = False,
    css_class: str = "",
) -> list[str]:
    if not items:
        return []
    class_attr = f" class=\"{css_class}\"" if css_class else ""
    out = [f"<p>{escape(title)}:</p>", f"<ul{class_attr}>"]
    for item in items:
        text = escape(truncate(item))
        if code:
            text = f"<code>{text}</code>"
        out.append(f"<li>{text}</li>")
    out.append("</ul>")
    return out


def write_static_report(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report["content"], encoding="utf-8", newline="\n")


def add_strings(out: list[str], value: Any) -> None:
    if value is None:
        return
    if isinstance(value, str):
        if value:
            out.append(value)
        return
    if isinstance(value, list | tuple):
        for item in value:
            add_strings(out, item)


def dict_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [item for item in value if isinstance(item, dict)]


def string_items(value: Any) -> list[str]:
    out: list[str] = []
    add_strings(out, value)
    return out


def related_addresses(item: dict[str, Any]) -> list[str]:
    values: list[str] = []
    add_strings(values, item.get("related_addresses"))
    add_strings(values, item.get("bank_address"))
    add_strings(values, item.get("address"))
    return unique_list(values)


def address_suffix(item: dict[str, Any]) -> str:
    addresses = related_addresses(item)
    if not addresses:
        return ""
    return " addresses=" + ", ".join(addresses[:4])


def trace_synthesis_related_sources(route: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            *string_items(route.get("source_symbols")),
            *source_mem_origins(route),
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


def semantic_suffix(item: dict[str, Any]) -> str:
    factors = string_items(item.get("semantic_factors"))
    if not factors and not item.get("semantic_score"):
        return ""
    if factors:
        labels = ", ".join(str(factor).split(":", 1)[0] for factor in factors[:3])
        return f" semantic={item.get('semantic_score', 0)}[{labels}]"
    return f" semantic={item.get('semantic_score', 0)}"


def instruction_trace_output_path(report: dict[str, Any]) -> str:
    trace_output = report.get("trace_output") if isinstance(report.get("trace_output"), dict) else {}
    return str(trace_output.get("path") or "")


def unique_list(items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        normalized = str(item)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        out.append(normalized)
    return out


def truncate(value: str, limit: int = 180) -> str:
    text = " ".join(value.split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def escape(value: str) -> str:
    return html.escape(value, quote=True)
