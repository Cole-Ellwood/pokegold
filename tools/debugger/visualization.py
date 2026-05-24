from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from .catalog import ROOT
from .coverage import load_traces
from .reporting import load_reports


VISUALIZATION_FORMATS = {"markdown", "html"}


def build_visualization_report(
    *,
    reports: tuple[str, ...] = (),
    traces: tuple[str, ...] = (),
    output_format: str = "markdown",
    title: str = "Unified Pokemon Gold Romhack Debugger Visualization",
    max_items: int = 80,
    root: Path = ROOT,
) -> dict[str, Any]:
    if output_format not in VISUALIZATION_FORMATS:
        raise ValueError(f"unknown visualization format: {output_format}")

    loaded_reports, report_errors = load_reports(reports=reports, root=root)
    loaded_traces, trace_errors = load_traces(traces=traces, root=root)
    timeline = collect_timeline(loaded_reports=loaded_reports, loaded_traces=loaded_traces)
    waterfall = collect_waterfall(loaded_reports=loaded_reports)
    graph = collect_graph(loaded_reports=loaded_reports)
    lanes = collect_lanes(
        loaded_reports=loaded_reports,
        timeline=timeline,
        waterfall=waterfall,
        graph=graph,
    )
    timeline = sorted(timeline, key=timeline_sort_key)[:max_items]
    waterfall = sorted(waterfall, key=waterfall_sort_key)[:max_items]
    graph["nodes"] = graph["nodes"][:max_items]
    graph["edges"] = graph["edges"][:max_items]
    lane_summary = summarize_lanes(lanes)
    mermaid_timeline = render_timeline_mermaid(timeline)
    mermaid_graph = render_graph_mermaid(graph)
    content = render_markdown_visualization(
        title=title,
        root=root,
        reports=loaded_reports,
        traces=loaded_traces,
        timeline=timeline,
        waterfall=waterfall,
        graph=graph,
        lane_summary=lane_summary,
        mermaid_timeline=mermaid_timeline,
        mermaid_graph=mermaid_graph,
        errors=[*report_errors, *trace_errors],
    )
    if output_format == "html":
        content = render_html_visualization(
            title=title,
            root=root,
            reports=loaded_reports,
            traces=loaded_traces,
            timeline=timeline,
            waterfall=waterfall,
            graph=graph,
            lane_summary=lane_summary,
            mermaid_timeline=mermaid_timeline,
            mermaid_graph=mermaid_graph,
            errors=[*report_errors, *trace_errors],
        )
    errors = unique_list([*report_errors, *trace_errors])
    warnings = []
    if not timeline and not waterfall and not graph["nodes"]:
        warnings.append("no visualization items were produced from the supplied inputs")
    return {
        "schema_version": 1,
        "kind": "unified_debugger_visualization",
        "root": str(root),
        "valid": not errors,
        "format": output_format,
        "title": title,
        "report_count": len(reports),
        "loaded_report_count": len(loaded_reports),
        "trace_count": len(loaded_traces),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "timeline_event_count": len(timeline),
        "waterfall_step_count": len(waterfall),
        "graph_node_count": len(graph["nodes"]),
        "graph_edge_count": len(graph["edges"]),
        "interactive": output_format == "html",
        "inspector_item_count": inspector_item_count(
            timeline=timeline,
            waterfall=waterfall,
            graph=graph,
        ),
        "lane_summary": lane_summary,
        "timeline": timeline,
        "waterfall": waterfall,
        "graph": graph,
        "mermaid_timeline": mermaid_timeline,
        "mermaid_graph": mermaid_graph,
        "content": content,
        "known_limits": [
            "HTML output includes a self-contained filterable evidence inspector; Markdown output remains static.",
            "This is still not a full interactive emulator/TUI or canvas replay inspector.",
            "Trace timelines are only as precise as the frames, events, or ordering present in the input reports.",
        ],
    }


def collect_timeline(
    *,
    loaded_reports: list[dict[str, Any]],
    loaded_traces: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    timeline: list[dict[str, Any]] = []
    for loaded in loaded_reports:
        collect_report_timeline(loaded["data"], source=loaded["source"], out=timeline)
    for loaded in loaded_traces:
        collect_trace_timeline(loaded["data"], source=loaded["source"], out=timeline)
    return timeline


def collect_report_timeline(data: dict[str, Any], *, source: str, out: list[dict[str, Any]]) -> None:
    kind = data.get("kind", "")
    for next_step in embedded_next_step_reports(data):
        collect_report_timeline(next_step, source=source, out=out)
    if kind == "unified_debugger_watch_report":
        for event in dict_items(data.get("events")):
            out.append(
                timeline_event(
                    lane="runtime",
                    event_type="watch",
                    title=f"{event.get('watch', '<watch>')} {event.get('old_hex', '')}->{event.get('new_hex', '')}",
                    source=source,
                    frame=event.get("frame"),
                    detail=(
                        f"{event.get('pc_bank_address', '')} {event.get('pc_label', '')} "
                        f"context={event.get('dynamic_context', {}).get('context_frame_count', 0)}"
                    ).strip(),
                    symbols=[str(event.get("watch", "")), str(event.get("pc_label", ""))],
                    severity=70,
                )
            )
    elif kind == "unified_debugger_capability_report":
        ready = bool(data.get("ready"))
        status_counts = status_counts_text(data)
        for capability in incomplete_capabilities(data):
            status = str(capability.get("status", "partial"))
            out.append(
                timeline_event(
                    lane="readiness",
                    event_type=f"capability_{status}",
                    title=f"Capability {status}: {capability_title(capability)}",
                    source=source,
                    detail=" ".join(
                        part
                        for part in (
                            f"ready={ready}",
                            status_counts,
                            first_gap(capability),
                        )
                        if part
                    ),
                    symbols=string_items(capability.get("id")),
                    files=string_items(capability.get("evidence")),
                    severity=78 if status == "missing" else 64,
                )
            )
    elif kind == "unified_debugger_next_step":
        for index, candidate in enumerate(next_step_candidates(data)):
            out.append(
                timeline_event(
                    lane="workflow",
                    event_type="next_step",
                    title=f"Next proof path: {candidate_title(candidate)}",
                    source=source,
                    order=index,
                    detail=next_step_detail(candidate),
                    symbols=string_items(candidate.get("matched_lane")),
                    severity=52,
                )
            )
    elif kind == "unified_debugger_replay_plan":
        watch_report = data.get("watch_report")
        if isinstance(watch_report, dict):
            collect_report_timeline(watch_report, source=source, out=out)
        for phase in dict_items(data.get("phase_steps")):
            for index, step in enumerate(dict_items(phase.get("steps"))):
                out.append(
                    timeline_event(
                        lane="workflow",
                        event_type="phase_step",
                        title=f"{phase.get('phase', 'phase')}: {step.get('command', '')}",
                        source=source,
                        order=index,
                        detail=str(step.get("reason", "")),
                        severity=35,
                    )
                )
    elif kind == "unified_debugger_causal_explanation":
        for path in dict_items(data.get("paths")):
            out.append(
                timeline_event(
                    lane="causal",
                    event_type="causal_path",
                    title=str(path.get("title", "")),
                    source=source,
                    detail=f"score={path.get('score', 0)} confidence={path.get('confidence', 0)}",
                    symbols=string_items(path.get("related_symbols")),
                    files=string_items(path.get("related_files")),
                    severity=int(path.get("score", 0)),
                )
            )
    elif kind == "unified_debugger_trace_index":
        for item in dict_items(data.get("reverse_attributions")):
            out.append(
                timeline_event(
                    lane="causal",
                    event_type="reverse_attribution",
                    title=str(item.get("title", "")),
                    source=source,
                    detail=f"contributors={item.get('contributor_count', 0)} confidence={item.get('confidence', 0)}",
                    symbols=string_items(item.get("related_symbols")),
                    files=string_items(item.get("related_files")),
                    severity=72,
                )
            )
    elif kind in {"unified_debugger_taint_report", "unified_debugger_dynamic_taint_report"}:
        for path in dict_items(data.get("paths")):
            out.append(
                timeline_event(
                    lane="causal",
                    event_type="taint_path",
                    title=str(path.get("title", "")),
                    source=source,
                    detail=f"contributors={len(dict_items(path.get('contributors')))} confidence={path.get('confidence', 0)}",
                    symbols=string_items(path.get("related_symbols")),
                    files=string_items(path.get("related_files")),
                    severity=int(path.get("score", 0)),
                )
            )
        for attribution in dict_items(data.get("write_attributions")):
            out.append(
                timeline_event(
                    lane="causal",
                    event_type="dynamic_write",
                    title=f"{attribution.get('target', '<sink>')} written at {attribution.get('pc_label', '<pc>')}",
                    source=source,
                    order=attribution.get("seq"),
                    detail=f"{attribution.get('mnemonic', '')} address=${attribution.get('address', '')}",
                    symbols=string_items(attribution.get("related_symbols")),
                    files=string_items(attribution.get("related_files")),
                    severity=int(attribution.get("score", 0)),
                )
            )
    elif kind == "unified_debugger_instruction_trace":
        collect_instruction_trace_validation_timeline(data, source=source, out=out)
        for function in dict_items(data.get("functions")):
            out.append(
                timeline_event(
                    lane="instruction_trace",
                    event_type="instruction_plan",
                    title=f"{function.get('symbol', '<function>')} instruction trace plan",
                    source=source,
                    detail=f"instructions={function.get('instruction_count', 0)} hooks={function.get('hook_count', 0)}",
                    symbols=[str(function.get("symbol", ""))],
                    severity=54,
                )
            )
        for record in dict_items(data.get("sample_records")):
            out.append(
                timeline_event(
                    lane="instruction_trace",
                    event_type="instruction",
                    title=f"{record.get('pc_label', '<pc>')} {record.get('mnemonic', '')}",
                    source=source,
                    order=record.get("seq"),
                    detail=str(record.get("pc_bank_address", "")),
                    symbols=[str(record.get("function", "")), str(record.get("pc_label", ""))],
                    severity=58,
                )
            )
    elif kind == "unified_debugger_impact_report":
        for item in dict_items(data.get("items")):
            out.append(
                timeline_event(
                    lane="impact",
                    event_type=str(item.get("type", "impact")),
                    title=str(item.get("title", "")),
                    source=source,
                    detail=f"impact={item.get('impact_score', 0)} surface={item.get('surface', '')}",
                    symbols=string_items(item.get("related_symbols")),
                    files=string_items(item.get("related_files")),
                    severity=int(item.get("impact_score", 0)),
                )
            )
    elif kind == "unified_debugger_coverage_report":
        for target in dict_items(data.get("targets")):
            out.append(
                timeline_event(
                    lane="coverage",
                    event_type=str(target.get("status", "target")),
                    title=f"{target.get('type', 'target')} {target.get('id', '')}",
                    source=source,
                    detail=", ".join(string_items(target.get("evidence"))[:2]),
                    symbols=[str(target.get("id", ""))] if target.get("type") == "symbol" else [],
                    files=[str(target.get("id", ""))] if target.get("type") == "source_file" else [],
                    severity=60 if target.get("status") == "uncovered" else 30,
                )
            )
    elif kind == "unified_debugger_gate_plan":
        for step in dict_items(data.get("steps")):
            out.append(
                timeline_event(
                    lane="gate",
                    event_type=str(step.get("status", "planned")),
                    title=str(step.get("command", "")),
                    source=source,
                    detail=str(step.get("title", "")),
                    severity=90 if step.get("status") == "failed" else 35,
                )
            )
    elif kind == "unified_debugger_minimization_plan":
        for step in dict_items(data.get("steps")):
            out.append(
                timeline_event(
                    lane="minimize",
                    event_type=str(step.get("phase", "step")),
                    title=str(step.get("command", "")),
                    source=source,
                    detail=str(step.get("reason", "")),
                    severity=45,
                )
            )
    elif kind == "unified_debugger_fuzz_plan":
        for campaign in dict_items(data.get("campaigns")):
            out.append(
                timeline_event(
                    lane="fuzz",
                    event_type=str(campaign.get("proof_level", "campaign")),
                    title=str(campaign.get("title", campaign.get("id", ""))),
                    source=source,
                    detail=f"surface={campaign.get('surface', '')} cases={campaign.get('case_budget', 0)}",
                    symbols=string_items(campaign.get("symbols")),
                    files=string_items(campaign.get("changed_files")),
                    severity=62 if campaign.get("proof_level") == "dynamic" else 42,
                )
            )
        for case in dict_items(data.get("fuzz_cases"))[:40]:
            out.append(
                timeline_event(
                    lane="fuzz",
                    event_type=str(case.get("fuzz_type", "case")),
                    title=str(case.get("id", "")),
                    source=source,
                    detail=", ".join(string_items(case.get("expectations"))[:2]),
                    symbols=string_items(case.get("symbols")),
                    files=string_items(case.get("changed_file")),
                    severity=45 if case.get("proof_level") == "dynamic" else 30,
                )
            )
    elif kind == "unified_debugger_compare_plan":
        for match in dict_items(data.get("matches")):
            out.append(
                timeline_event(
                    lane="differential",
                    event_type=str(match.get("id", "mirror")),
                    title=str(match.get("title", match.get("id", ""))),
                    source=source,
                    detail=", ".join(string_items(match.get("gaps"))[:2]),
                    severity=55 if match.get("gaps") else 35,
                )
            )
    elif kind == "unified_debugger_content_mirror":
        for invariant in dict_items(data.get("invariants")):
            status = str(invariant.get("status", ""))
            if status == "passed":
                continue
            out.append(
                timeline_event(
                    lane="content",
                    event_type=str(invariant.get("type", "invariant")),
                    title=str(invariant.get("title", invariant.get("id", ""))),
                    source=source,
                    order=int(invariant.get("line", 0)),
                    detail=", ".join(string_items(invariant.get("evidence"))[:2]),
                    symbols=string_items(invariant.get("related_symbols")),
                    files=string_items(invariant.get("related_files")) or string_items(invariant.get("source_file")),
                    severity=int(invariant.get("severity", 40 if status == "warning" else 70)),
                )
            )
    elif kind == "unified_debugger_content_scenarios":
        for scenario in dict_items(data.get("scenarios")):
            out.append(
                timeline_event(
                    lane="content",
                    event_type=str(scenario.get("scenario_type", "scenario")),
                    title=str(scenario.get("id", "")),
                    source=source,
                    order=int(scenario.get("line", 0)),
                    detail=", ".join(string_items(scenario.get("expected"))[:2]),
                    files=string_items(scenario.get("source_file")),
                    severity=44,
                )
            )
    elif kind == "unified_debugger_content_state_materialization":
        collect_content_state_timeline(data, source=source, out=out)
    elif kind == "unified_debugger_state_space":
        collect_state_space_timeline(data, source=source, out=out)


def collect_instruction_trace_validation_timeline(data: dict[str, Any], *, source: str, out: list[dict[str, Any]]) -> None:
    validation = data.get("execution_validation") if isinstance(data.get("execution_validation"), dict) else {}
    if not validation.get("attempted"):
        return
    status = instruction_trace_validation_status(validation)
    out.append(
        timeline_event(
            lane="instruction_trace",
            event_type=status["event_type"],
            title=status["title"],
            source=source,
            detail=instruction_trace_validation_detail(data, validation),
            symbols=instruction_trace_validation_symbols(data, validation),
            files=[],
            severity=int(status["severity"]),
        )
    )
    if validation.get("trace_record_limit_hit"):
        out.append(
            timeline_event(
                lane="instruction_trace",
                event_type="validation_limit",
                title="Instruction trace reached the record limit",
                source=source,
                detail=instruction_trace_validation_detail(data, validation),
                symbols=instruction_trace_validation_symbols(data, validation),
                severity=68,
            )
        )


def instruction_trace_validation_status(validation: dict[str, Any]) -> dict[str, Any]:
    if not validation.get("hit"):
        severity = 80 if validation.get("required") else 74
        return {
            "event_type": "validation_miss",
            "title": "Instruction trace hooks did not fire",
            "severity": severity,
        }
    if string_items(validation.get("missing_function_symbols")):
        return {
            "event_type": "validation_partial",
            "title": "Instruction trace missed selected routines",
            "severity": 64,
        }
    if validation.get("ready_for_dynamic_taint"):
        return {
            "event_type": "validation_ready",
            "title": "Instruction trace ready for dynamic taint",
            "severity": 60,
        }
    return {
        "event_type": "validation_hit",
        "title": "Instruction trace hooks fired",
        "severity": 55,
    }


def instruction_trace_validation_detail(data: dict[str, Any], validation: dict[str, Any]) -> str:
    parts = [
        f"captured={validation.get('captured_frame_count', data.get('captured_frame_count', 0))}",
        f"hooks={validation.get('planned_hook_count', 0)}",
        f"hit={validation.get('hit')}",
        f"hit_functions={','.join(string_items(validation.get('hit_function_symbols'))[:6])}",
        f"missing={','.join(string_items(validation.get('missing_function_symbols'))[:6])}",
        f"watches={','.join(string_items(validation.get('watch_symbols'))[:6])}",
        f"trace={instruction_trace_output_path(data)}",
        f"save={instruction_trace_save_state(data)}",
    ]
    return " ".join(part for part in parts if part and not part.endswith("="))


def instruction_trace_validation_symbols(data: dict[str, Any], validation: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            *string_items(validation.get("hit_function_symbols")),
            *string_items(validation.get("missing_function_symbols")),
            *string_items(validation.get("watch_symbols")),
            *[
                str(function.get("symbol", ""))
                for function in dict_items(data.get("functions"))
                if function.get("symbol")
            ],
        ]
    )


def instruction_trace_output_path(data: dict[str, Any]) -> str:
    trace_output = data.get("trace_output") if isinstance(data.get("trace_output"), dict) else {}
    return str(trace_output.get("path") or "")


def instruction_trace_save_state(data: dict[str, Any]) -> str:
    return str(data.get("effective_save_state") or data.get("save_state") or "")


def collect_instruction_trace_waterfall(data: dict[str, Any], *, source: str, out: list[dict[str, Any]]) -> None:
    validation = data.get("execution_validation") if isinstance(data.get("execution_validation"), dict) else {}
    if validation:
        if validation.get("attempted"):
            status = instruction_trace_validation_status(validation)
            title = str(status["title"])
        else:
            title = "Instruction trace validation planned"
        out.append(
            waterfall_step(
                phase="instruction-trace",
                title=title,
                source=source,
                status=instruction_trace_waterfall_status(validation),
                detail=instruction_trace_validation_detail(data, validation),
                order=0,
            )
        )
    for index, command in enumerate(string_items(data.get("commands"))):
        out.append(
            waterfall_step(
                phase="instruction-trace",
                title=command,
                source=source,
                status=command_status(command),
                detail="capture selected instruction hooks from a positioned ROM state",
                order=index + 1,
            )
        )


def instruction_trace_waterfall_status(validation: dict[str, Any]) -> str:
    if not validation.get("attempted"):
        return "planned"
    if not validation.get("hit"):
        return "missed"
    if validation.get("trace_record_limit_hit"):
        return "limit"
    if string_items(validation.get("missing_function_symbols")):
        return "partial"
    if validation.get("ready_for_dynamic_taint"):
        return "ready"
    return "hit"


def collect_content_state_timeline(data: dict[str, Any], *, source: str, out: list[dict[str, Any]]) -> None:
    execution = data.get("execution") if isinstance(data.get("execution"), dict) else {}
    out_state = str(execution.get("out_state") or data.get("out_state") or "")
    for materialization in dict_items(data.get("materializations")):
        status = str(materialization.get("status", "planned"))
        scenario_id = str(materialization.get("scenario_id", "") or materialization.get("precondition_id", "content_state"))
        errors = string_items(materialization.get("errors"))
        detail = "; ".join(
            part
            for part in [
                f"precondition={materialization.get('precondition_kind', '')}",
                f"map={materialization.get('map_name', '')}",
                ", ".join(content_state_patch_evidence(materialization.get("patches"))[:4]),
                ", ".join(errors[:2]),
            ]
            if part
        )
        out.append(
            timeline_event(
                lane="content_state",
                event_type=status,
                title=f"{scenario_id} {status}",
                source=source,
                detail=detail,
                symbols=content_state_patch_symbols(materialization.get("patches")),
                files=content_state_related_files(materialization),
                severity=content_state_severity(status=status, errors=errors),
            )
        )
    if bool(data.get("executed") or execution.get("executed")):
        applied_patches = dict_items(execution.get("applied_patches"))
        out.append(
            timeline_event(
                lane="runtime",
                event_type="content_state_executed",
                title=f"Patched content state saved: {out_state or source}",
                source=source,
                detail=f"applied_patches={len(applied_patches)} "
                + ", ".join(content_state_patch_evidence(applied_patches)[:4]),
                symbols=content_state_patch_symbols(applied_patches),
                files=[],
                severity=62,
            )
        )


def collect_content_state_graph(
    data: dict[str, Any],
    *,
    source: str,
    nodes: dict[str, dict[str, Any]],
    edges: dict[tuple[str, str, str], dict[str, Any]],
) -> None:
    execution = data.get("execution") if isinstance(data.get("execution"), dict) else {}
    out_state = str(execution.get("out_state") or data.get("out_state") or "")
    if out_state:
        add_graph_node(nodes, out_state, out_state, "save_state", source)
    for materialization in dict_items(data.get("materializations")):
        scenario_id = str(materialization.get("scenario_id", "") or materialization.get("precondition_id", "content_state"))
        source_path = str(materialization.get("source_file", ""))
        map_resolution = materialization.get("map_resolution") if isinstance(materialization.get("map_resolution"), dict) else {}
        map_table = str(map_resolution.get("source_file", ""))
        add_graph_node(nodes, scenario_id, scenario_id, "content_state_materialization", source)
        if source_path:
            add_graph_node(nodes, source_path, source_path, "content_source", source)
            add_graph_edge(edges, source_path, scenario_id, "materializes", source)
        if map_table:
            add_graph_node(nodes, map_table, map_table, "map_index", source)
            add_graph_edge(edges, map_table, scenario_id, "resolves_map", source)
        for patch in dict_items(materialization.get("patches")):
            symbol = str(patch.get("symbol", ""))
            if not symbol:
                continue
            add_graph_node(nodes, symbol, symbol, "runtime_state_patch", source)
            add_graph_edge(edges, scenario_id, symbol, f"patches {content_state_patch_value(patch)}", source)
            if out_state:
                add_graph_edge(edges, symbol, out_state, "saved_to", source)


def collect_state_space_timeline(data: dict[str, Any], *, source: str, out: list[dict[str, Any]]) -> None:
    state_space = data.get("state_space") if isinstance(data.get("state_space"), dict) else {}
    execution = data.get("execution") if isinstance(data.get("execution"), dict) else {}
    out_state = str(execution.get("out_state") or data.get("out_state") or state_space.get("out_state") or "")
    patches = state_space_patch_records(data)
    errors = string_items(data.get("errors"))
    scenario_id = state_space_scenario_ids(data)[0] if state_space_scenario_ids(data) else "state_space"
    status = "executed" if bool(data.get("executed") or execution.get("executed")) else ("blocked" if errors or not data.get("valid", True) else "ready")
    if patches or errors:
        out.append(
            timeline_event(
                lane="state_space",
                event_type=status,
                title=f"{scenario_id} {status}",
                source=source,
                detail=", ".join([*content_state_patch_evidence(patches)[:4], *errors[:2]]),
                symbols=content_state_patch_symbols(patches),
                files=state_space_source_files(data),
                severity=content_state_severity(status="blocked" if status == "blocked" else "ready", errors=errors),
            )
        )
    if bool(data.get("executed") or execution.get("executed")):
        applied_patches = dict_items(execution.get("applied_patches")) or [patch for patch in patches if patch.get("applied")]
        out.append(
            timeline_event(
                lane="runtime",
                event_type="state_space_executed",
                title=f"Patched state-space saved: {out_state or source}",
                source=source,
                detail=f"applied_patches={len(applied_patches)} "
                + ", ".join(content_state_patch_evidence(applied_patches)[:4]),
                symbols=content_state_patch_symbols(applied_patches),
                files=state_space_source_files(data),
                severity=62,
            )
        )


def collect_state_space_graph(
    data: dict[str, Any],
    *,
    source: str,
    nodes: dict[str, dict[str, Any]],
    edges: dict[tuple[str, str, str], dict[str, Any]],
) -> None:
    state_space = data.get("state_space") if isinstance(data.get("state_space"), dict) else {}
    execution = data.get("execution") if isinstance(data.get("execution"), dict) else {}
    out_state = str(execution.get("out_state") or data.get("out_state") or state_space.get("out_state") or "")
    scenario_id = state_space_scenario_ids(data)[0] if state_space_scenario_ids(data) else "state_space"
    add_graph_node(nodes, scenario_id, scenario_id, "state_space_materialization", source)
    if out_state:
        add_graph_node(nodes, out_state, out_state, "save_state", source)
    for source_file in state_space_source_files(data):
        add_graph_node(nodes, source_file, source_file, "content_source", source)
        add_graph_edge(edges, source_file, scenario_id, "informs", source)
    for patch in state_space_patch_records(data):
        symbol = str(patch.get("symbol", ""))
        if not symbol:
            continue
        add_graph_node(nodes, symbol, symbol, "runtime_state_patch", source)
        add_graph_edge(edges, scenario_id, symbol, f"patches {content_state_patch_value(patch)}", source)
        if out_state:
            add_graph_edge(edges, symbol, out_state, "saved_to", source)


def state_space_patch_records(data: dict[str, Any]) -> list[dict[str, Any]]:
    state_space = data.get("state_space") if isinstance(data.get("state_space"), dict) else {}
    execution = data.get("execution") if isinstance(data.get("execution"), dict) else {}
    return [
        *dict_items(data.get("state_patches")),
        *dict_items(state_space.get("patches")),
        *dict_items(state_space.get("state_patches")),
        *dict_items(execution.get("applied_patches")),
    ]


def state_space_scenario_ids(data: dict[str, Any]) -> list[str]:
    state_space = data.get("state_space") if isinstance(data.get("state_space"), dict) else {}
    return unique_list(
        [
            str(data.get("scenario_id", "")),
            *string_items(state_space.get("scenario_ids")),
            *[
                str(patch.get("scenario_id", ""))
                for patch in state_space_patch_records(data)
                if patch.get("scenario_id")
            ],
        ]
    )


def state_space_source_files(data: dict[str, Any]) -> list[str]:
    state_space = data.get("state_space") if isinstance(data.get("state_space"), dict) else {}
    return unique_list(
        [
            *string_items(data.get("source_files")),
            *string_items(state_space.get("source_files")),
            *[
                str(patch.get("source_file", ""))
                for patch in state_space_patch_records(data)
                if patch.get("source_file")
            ],
        ]
    )


def content_state_severity(*, status: str, errors: list[str]) -> int:
    if errors or status == "blocked":
        return 68
    if status == "ready":
        return 58
    return 45


def content_state_related_files(materialization: dict[str, Any]) -> list[str]:
    map_resolution = materialization.get("map_resolution") if isinstance(materialization.get("map_resolution"), dict) else {}
    return unique_list(
        [
            path
            for path in [
                str(materialization.get("source_file", "")),
                str(map_resolution.get("source_file", "")),
            ]
            if path
        ]
    )


def content_state_patch_symbols(raw_patches: Any) -> list[str]:
    return unique_list(
        [
            str(patch.get("symbol", ""))
            for patch in dict_items(raw_patches)
            if patch.get("symbol")
        ]
    )


def content_state_patch_evidence(raw_patches: Any) -> list[str]:
    out = []
    for patch in dict_items(raw_patches):
        symbol = str(patch.get("symbol", ""))
        if not symbol:
            continue
        address = str(patch.get("bank_address") or patch.get("address") or "")
        suffix = f" @{address}" if address else ""
        out.append(f"{symbol}={content_state_patch_value(patch)}{suffix}")
    return out


def content_state_patch_value(patch: dict[str, Any]) -> str:
    value_hex = str(patch.get("value_hex") or "")
    if value_hex:
        return f"0x{value_hex}"
    if patch.get("value") is not None:
        return str(patch.get("value"))
    return "<unknown>"


def collect_trace_timeline(data: Any, *, source: str, out: list[dict[str, Any]]) -> None:
    for index, item in enumerate(trace_observations(data)[:200]):
        out.append(
            timeline_event(
                lane="trace",
                event_type="observation",
                title=item.get("symbol") or item.get("source_file") or item.get("rule_id") or "trace observation",
                source=source,
                order=index,
                detail=", ".join(part for part in (item.get("source_file"), item.get("rule_id")) if part),
                symbols=[item.get("symbol", "")],
                files=[item.get("source_file", "")],
                severity=30,
            )
        )


def collect_waterfall(*, loaded_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    for loaded in loaded_reports:
        data = loaded["data"]
        source = loaded["source"]
        for next_step in embedded_next_step_reports(data):
            steps.extend(collect_waterfall(loaded_reports=[{"data": next_step, "source": source}]))
        for phase in dict_items(data.get("phase_steps")):
            for index, step in enumerate(dict_items(phase.get("steps"))):
                steps.append(
                    waterfall_step(
                        phase=str(phase.get("phase", phase.get("title", "phase"))),
                        title=str(step.get("command", "")),
                        source=source,
                        status="runnable" if step.get("runnable") else "needs-input",
                        detail=str(step.get("reason", "")),
                        order=index,
                    )
                )
        for index, step in enumerate(dict_items(data.get("steps"))):
            steps.append(
                waterfall_step(
                    phase=str(step.get("phase", step.get("match_id", "step"))),
                    title=str(step.get("command", "")),
                    source=source,
                    status=str(step.get("status", "planned")),
                    detail=str(step.get("reason", step.get("title", ""))),
                    order=index,
                )
            )
        for scenario in dict_items(data.get("scenarios")):
            scenario_id = str(scenario.get("id", "scenario"))
            for index, probe in enumerate(dict_items(scenario.get("behavioral_probes"))):
                steps.append(
                    waterfall_step(
                        phase=str(probe.get("phase", "probe")),
                        title=str(probe.get("command", "")),
                        source=source,
                        status="runnable" if probe.get("runnable") else "needs-input",
                        detail=f"{scenario_id}: {probe.get('reason', '')}",
                        order=index,
                    )
                )
        if data.get("kind") == "unified_debugger_content_state_materialization":
            for index, command in enumerate(string_items(data.get("commands"))):
                steps.append(
                    waterfall_step(
                        phase="content-state",
                        title=command,
                        source=source,
                        status=command_status(command),
                        detail="materialize or execute a positioned content-state save",
                        order=index,
                    )
                )
            command_offset = len(string_items(data.get("commands")))
            for materialization in dict_items(data.get("materializations")):
                scenario_id = str(materialization.get("scenario_id", "content_state"))
                status = str(materialization.get("status", "planned"))
                for index, command in enumerate(string_items(materialization.get("commands"))):
                    steps.append(
                        waterfall_step(
                            phase="content-state",
                            title=command,
                            source=source,
                            status=command_status(command),
                            detail=f"{scenario_id}: {status}",
                            order=command_offset + index,
                        )
                    )
        if data.get("kind") == "unified_debugger_instruction_trace":
            collect_instruction_trace_waterfall(data, source=source, out=steps)
        if data.get("kind") == "unified_debugger_capability_report":
            for capability_index, capability in enumerate(incomplete_capabilities(data)):
                for command_index, command in enumerate(string_items(capability.get("commands"))[:3]):
                    steps.append(
                        waterfall_step(
                            phase="capability-audit",
                            title=command,
                            source=source,
                            status=command_status(command),
                            detail=(
                                f"{capability.get('status', 'partial')} capability: "
                                f"{capability.get('id', '')} - {first_gap(capability)}"
                            ).strip(),
                            order=capability_index * 10 + command_index,
                        )
                    )
        if data.get("kind") == "unified_debugger_next_step":
            for candidate_index, candidate in enumerate(next_step_candidates(data)):
                first_command = str(candidate.get("first_command", ""))
                if first_command:
                    steps.append(
                        waterfall_step(
                            phase="prove",
                            title=first_command,
                            source=source,
                            status=command_status(first_command),
                            detail=next_step_detail(candidate),
                            order=candidate_index * 10,
                        )
                    )
                regression_gate = str(candidate.get("regression_gate", ""))
                if regression_gate:
                    steps.append(
                        waterfall_step(
                            phase="verify",
                            title=regression_gate,
                            source=source,
                            status=command_status(regression_gate),
                            detail=f"Regression gate for {candidate_title(candidate)}.",
                            order=candidate_index * 10 + 1,
                        )
                    )
                escalation_command = str(candidate.get("escalation_command", ""))
                if escalation_command:
                    steps.append(
                        waterfall_step(
                            phase="escalate",
                            title=escalation_command,
                            source=source,
                            status=command_status(escalation_command),
                            detail=f"Escalate after the first proof path for {candidate_title(candidate)}.",
                            order=candidate_index * 10 + 2,
                        )
                    )
    return steps


def collect_graph(*, loaded_reports: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[tuple[str, str, str], dict[str, Any]] = {}
    for loaded in loaded_reports:
        data = loaded["data"]
        source = loaded["source"]
        kind = data.get("kind", "")
        for next_step in embedded_next_step_reports(data):
            nested_graph = collect_graph(loaded_reports=[{"data": next_step, "source": source}])
            for node in nested_graph["nodes"]:
                nodes[node["id"]] = node
            for edge in nested_graph["edges"]:
                edges[(edge["from"], edge["to"], edge["relation"])] = edge
        if kind == "unified_debugger_causal_explanation":
            for path in dict_items(data.get("paths")):
                for item in dict_items(path.get("nodes")):
                    add_graph_node(nodes, item.get("id", ""), item.get("label", ""), item.get("type", ""), source)
                for edge in dict_items(path.get("edges")):
                    add_graph_edge(edges, edge.get("from", ""), edge.get("to", ""), edge.get("relation", ""), source)
        elif kind == "unified_debugger_causal_slice":
            for target in dict_items(data.get("targets")):
                target_name = str(target.get("resolved") or target.get("query") or "")
                add_graph_node(nodes, target_name, target_name, "symbol", source)
                for edge in [*dict_items(target.get("incoming")), *dict_items(target.get("outgoing"))]:
                    add_graph_node(nodes, str(edge.get("source", "")), str(edge.get("source", "")), "symbol", source)
                    add_graph_node(nodes, str(edge.get("target", "")), str(edge.get("target", "")), "symbol", source)
                    add_graph_edge(edges, str(edge.get("source", "")), str(edge.get("target", "")), str(edge.get("access", "")), source)
        elif kind in {"unified_debugger_taint_report", "unified_debugger_dynamic_taint_report"}:
            for path in dict_items(data.get("paths")):
                target = str(path.get("target", ""))
                add_graph_node(nodes, target, target, "taint_target", source)
                for contributor in dict_items(path.get("contributors")):
                    symbol = str(contributor.get("symbol", ""))
                    add_graph_node(nodes, symbol, symbol, "taint_source", source)
                    add_graph_edge(edges, symbol, target, str(contributor.get("relation", "taints")), source)
            for attribution in dict_items(data.get("write_attributions")):
                target = str(attribution.get("target", ""))
                pc_label = str(attribution.get("pc_label", ""))
                write_id = str(attribution.get("id") or f"{target}:{pc_label}:{attribution.get('seq', '')}")
                add_graph_node(nodes, target, target, "dynamic_write_target", source)
                add_graph_node(nodes, pc_label, pc_label, "instruction", source)
                add_graph_node(nodes, write_id, str(attribution.get("mnemonic", write_id)), "dynamic_write", source)
                add_graph_edge(edges, pc_label, write_id, "executes", source)
                add_graph_edge(edges, write_id, target, "writes", source)
                for operand in dict_items(attribution.get("source_operands")):
                    operand_label = source_operand_label(operand)
                    add_graph_node(nodes, operand_label, operand_label, "write_operand", source)
                    add_graph_edge(edges, operand_label, write_id, "feeds", source)
        elif kind == "unified_debugger_instruction_trace":
            collect_instruction_trace_validation_graph(data, source=source, nodes=nodes, edges=edges)
            for function in dict_items(data.get("functions")):
                function_name = str(function.get("symbol", ""))
                add_graph_node(nodes, function_name, function_name, "instruction_function", source)
                for instruction in dict_items(function.get("instructions"))[:24]:
                    instruction_id = str(instruction.get("bank_address", ""))
                    add_graph_node(nodes, instruction_id, f"{instruction_id} {instruction.get('mnemonic', '')}", "instruction", source)
                    add_graph_edge(edges, function_name, instruction_id, "hooks", source)
            for watch in dict_items(data.get("watches")):
                watch_name = str(watch.get("name", ""))
                add_graph_node(nodes, watch_name, watch_name, "watch", source)
                for function in dict_items(data.get("functions")):
                    add_graph_edge(edges, str(function.get("symbol", "")), watch_name, "watches", source)
        elif kind == "unified_debugger_coverage_report":
            for target in dict_items(data.get("targets")):
                target_id = str(target.get("id", ""))
                add_graph_node(nodes, target_id, target_id, str(target.get("status", "target")), source)
                for symbol in string_items(target.get("related_symbols")):
                    add_graph_node(nodes, symbol, symbol, "related_symbol", source)
                    add_graph_edge(edges, symbol, target_id, "covers", source)
                for path in string_items(target.get("related_files")):
                    add_graph_node(nodes, path, path, "related_file", source)
                    add_graph_edge(edges, path, target_id, "relates", source)
        elif kind == "unified_debugger_content_mirror":
            for source_file in dict_items(data.get("source_files")):
                source_path = str(source_file.get("path", ""))
                add_graph_node(nodes, source_path, source_path, "content_source", source)
            for invariant in dict_items(data.get("invariants")):
                if invariant.get("status") == "passed":
                    continue
                invariant_id = str(invariant.get("id", ""))
                title = str(invariant.get("title", invariant_id))
                source_path = str(invariant.get("source_file", ""))
                add_graph_node(nodes, invariant_id, title, str(invariant.get("type", "invariant")), source)
                add_graph_node(nodes, source_path, source_path, "content_source", source)
                add_graph_edge(edges, source_path, invariant_id, str(invariant.get("status", "checks")), source)
        elif kind == "unified_debugger_content_scenarios":
            for scenario in dict_items(data.get("scenarios")):
                scenario_id = str(scenario.get("id", ""))
                source_path = str(scenario.get("source_file", ""))
                title = str(scenario.get("scenario_type", scenario_id))
                add_graph_node(nodes, source_path, source_path, "content_source", source)
                add_graph_node(nodes, scenario_id, title, "content_scenario", source)
                add_graph_edge(edges, source_path, scenario_id, "generates", source)
                runtime_targets = scenario.get("runtime_targets") if isinstance(scenario.get("runtime_targets"), dict) else {}
                for symbol in string_items(runtime_targets.get("source_symbols")):
                    add_graph_node(nodes, symbol, symbol, "content_source_symbol", source)
                    add_graph_edge(edges, scenario_id, symbol, "defines", source)
                for symbol in string_items(runtime_targets.get("script_symbols")):
                    add_graph_node(nodes, symbol, symbol, "content_script_symbol", source)
                    add_graph_edge(edges, scenario_id, symbol, "triggers", source)
                for symbol in string_items(runtime_targets.get("trace_symbols")):
                    add_graph_node(nodes, symbol, symbol, "runtime_helper", source)
                    add_graph_edge(edges, scenario_id, symbol, "trace_probe", source)
                for symbol in string_items(runtime_targets.get("watch_symbols")):
                    add_graph_node(nodes, symbol, symbol, "runtime_watch", source)
                    add_graph_edge(edges, scenario_id, symbol, "watch_probe", source)
                for probe in dict_items(scenario.get("behavioral_probes")):
                    probe_id = f"{scenario_id}:{probe.get('id', 'probe')}"
                    add_graph_node(nodes, probe_id, str(probe.get("phase", probe_id)), "behavioral_probe", source)
                    add_graph_edge(edges, scenario_id, probe_id, str(probe.get("proof_level", "probes")), source)
        elif kind == "unified_debugger_content_state_materialization":
            collect_content_state_graph(data, source=source, nodes=nodes, edges=edges)
        elif kind == "unified_debugger_state_space":
            collect_state_space_graph(data, source=source, nodes=nodes, edges=edges)
        elif kind == "unified_debugger_capability_report":
            audit_id = f"{source}:capability_audit"
            ready_label = f"Debugger audit ready={bool(data.get('ready'))}"
            add_graph_node(nodes, audit_id, ready_label, "capability_audit", source)
            for capability in incomplete_capabilities(data):
                capability_id = f"{source}:capability:{capability.get('id', capability_title(capability))}"
                add_graph_node(
                    nodes,
                    capability_id,
                    capability_title(capability),
                    str(capability.get("status", "partial")),
                    source,
                )
                add_graph_edge(edges, audit_id, capability_id, str(capability.get("status", "partial")), source)
                for index, command in enumerate(string_items(capability.get("commands"))[:3]):
                    command_id = f"{capability_id}:command:{index}"
                    add_graph_node(nodes, command_id, command, "proof_command", source)
                    add_graph_edge(edges, capability_id, command_id, "proof_command", source)
        elif kind == "unified_debugger_next_step":
            symptom = str(data.get("symptom") or "<unspecified symptom>")
            symptom_id = f"{source}:symptom:{symptom}"
            add_graph_node(nodes, symptom_id, symptom, "symptom", source)
            for candidate in next_step_candidates(data):
                candidate_id = f"{source}:next:{candidate_title(candidate)}:{candidate.get('symptom_class', '')}"
                add_graph_node(nodes, candidate_id, candidate_title(candidate), "next_step", source)
                add_graph_edge(edges, symptom_id, candidate_id, "routes_to", source)
                first_command = str(candidate.get("first_command", ""))
                if first_command:
                    command_id = f"{candidate_id}:first"
                    add_graph_node(nodes, command_id, first_command, "proof_command", source)
                    add_graph_edge(edges, candidate_id, command_id, "first_command", source)
                for source_ref in string_items(candidate.get("source_refs"))[:6]:
                    source_ref_id = f"source_ref:{source_ref}"
                    add_graph_node(nodes, source_ref_id, source_ref, "source_ref", source)
                    add_graph_edge(edges, candidate_id, source_ref_id, "source_ref", source)
                for index, standard in enumerate(string_items(candidate.get("evidence_standard"))[:6]):
                    standard_id = f"{candidate_id}:evidence_standard:{index}"
                    add_graph_node(nodes, standard_id, standard, "evidence_standard", source)
                    add_graph_edge(edges, candidate_id, standard_id, "evidence_standard", source)
                for index, standard in enumerate(string_items(candidate.get("disproof_standard"))[:6]):
                    standard_id = f"{candidate_id}:disproof_standard:{index}"
                    add_graph_node(nodes, standard_id, standard, "disproof_standard", source)
                    add_graph_edge(edges, candidate_id, standard_id, "disproof_standard", source)
                regression_gate = str(candidate.get("regression_gate", ""))
                if regression_gate:
                    gate_id = f"{candidate_id}:regression"
                    add_graph_node(nodes, gate_id, regression_gate, "regression_gate", source)
                    add_graph_edge(edges, candidate_id, gate_id, "regression_gate", source)
                escalation_command = str(candidate.get("escalation_command", ""))
                if escalation_command:
                    escalation_id = f"{candidate_id}:escalation"
                    add_graph_node(nodes, escalation_id, escalation_command, "proof_command", source)
                    add_graph_edge(edges, candidate_id, escalation_id, "escalates", source)
    return {
        "nodes": sorted(nodes.values(), key=lambda item: (item["type"], item["label"])),
        "edges": sorted(edges.values(), key=lambda item: (item["from"], item["to"], item["relation"])),
    }


def collect_instruction_trace_validation_graph(
    data: dict[str, Any],
    *,
    source: str,
    nodes: dict[str, dict[str, Any]],
    edges: dict[tuple[str, str, str], dict[str, Any]],
) -> None:
    validation = data.get("execution_validation") if isinstance(data.get("execution_validation"), dict) else {}
    if not validation:
        return
    status = instruction_trace_validation_status(validation) if validation.get("attempted") else {
        "title": "Instruction trace validation",
        "event_type": "validation_planned",
        "severity": 0,
    }
    validation_id = f"{source}:instruction_trace_validation"
    add_graph_node(nodes, validation_id, str(status["title"]), "instruction_trace_validation", source)
    trace_path = instruction_trace_output_path(data)
    if trace_path:
        trace_output = data.get("trace_output") if isinstance(data.get("trace_output"), dict) else {}
        add_graph_node(nodes, trace_path, trace_path, "instruction_trace_output", source)
        relation = "writes_trace" if trace_output.get("written") else "plans_trace"
        add_graph_edge(edges, validation_id, trace_path, relation, source)
    save_state = instruction_trace_save_state(data)
    if save_state:
        add_graph_node(nodes, save_state, save_state, "save_state", source)
        add_graph_edge(edges, save_state, validation_id, "loads_state", source)
    for symbol in string_items(validation.get("hit_function_symbols")):
        add_graph_node(nodes, symbol, symbol, "instruction_hit", source)
        add_graph_edge(edges, symbol, validation_id, "hit", source)
    for symbol in string_items(validation.get("missing_function_symbols")):
        add_graph_node(nodes, symbol, symbol, "instruction_miss", source)
        add_graph_edge(edges, symbol, validation_id, "missed", source)
    for symbol in string_items(validation.get("watch_symbols")):
        add_graph_node(nodes, symbol, symbol, "watch", source)
        add_graph_edge(edges, validation_id, symbol, "observes", source)


def collect_lanes(
    *,
    loaded_reports: list[dict[str, Any]],
    timeline: list[dict[str, Any]],
    waterfall: list[dict[str, Any]],
    graph: dict[str, list[dict[str, Any]]],
) -> dict[str, dict[str, Any]]:
    lanes: dict[str, dict[str, Any]] = {}
    for item in timeline:
        lane = lanes.setdefault(item["lane"], {"count": 0, "max_severity": 0, "sources": set()})
        lane["count"] += 1
        lane["max_severity"] = max(int(lane["max_severity"]), int(item.get("severity", 0)))
        lane["sources"].add(item.get("source", ""))
    if waterfall:
        lane = lanes.setdefault("workflow", {"count": 0, "max_severity": 0, "sources": set()})
        lane["count"] += len(waterfall)
        lane["sources"].update(step.get("source", "") for step in waterfall)
    if graph["nodes"]:
        lane = lanes.setdefault("graph", {"count": 0, "max_severity": 0, "sources": set()})
        lane["count"] += len(graph["nodes"])
        lane["sources"].update(item.get("source", "") for item in graph["nodes"])
    for loaded in loaded_reports:
        lane = lanes.setdefault("inputs", {"count": 0, "max_severity": 0, "sources": set()})
        lane["count"] += 1
        lane["sources"].add(loaded["source"])
    return lanes


def summarize_lanes(lanes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for lane, item in lanes.items():
        out.append(
            {
                "lane": lane,
                "count": int(item["count"]),
                "max_severity": int(item.get("max_severity", 0)),
                "sources": sorted(str(source) for source in item.get("sources", set()) if source)[:8],
            }
        )
    return sorted(out, key=lambda item: (-item["max_severity"], item["lane"]))


def render_timeline_mermaid(timeline: list[dict[str, Any]]) -> str:
    if not timeline:
        return "timeline\n"
    lines = ["timeline", "    title Debugger Evidence Timeline"]
    for item in timeline[:40]:
        lane = mermaid_text(item["lane"])
        title = mermaid_text(item["title"])
        detail = mermaid_text(item.get("detail", ""))
        line = f"    {lane} : {title}"
        if detail:
            line += f" : {detail}"
        lines.append(line)
    return "\n".join(lines) + "\n"


def render_graph_mermaid(graph: dict[str, list[dict[str, Any]]]) -> str:
    if not graph["nodes"]:
        return "graph TD\n"
    lines = ["graph TD"]
    node_ids = {item["id"] for item in graph["nodes"][:80]}
    for item in graph["nodes"][:80]:
        lines.append(f'  {item["id"]}["{mermaid_text(item["label"])}"]')
    for edge in graph["edges"][:120]:
        if edge["from"] not in node_ids or edge["to"] not in node_ids:
            continue
        lines.append(f'  {edge["from"]} -->|{mermaid_text(edge["relation"])}| {edge["to"]}')
    return "\n".join(lines) + "\n"


def render_markdown_visualization(
    *,
    title: str,
    root: Path,
    reports: list[dict[str, Any]],
    traces: list[dict[str, Any]],
    timeline: list[dict[str, Any]],
    waterfall: list[dict[str, Any]],
    graph: dict[str, list[dict[str, Any]]],
    lane_summary: list[dict[str, Any]],
    mermaid_timeline: str,
    mermaid_graph: str,
    errors: list[str],
) -> str:
    lines = [
        f"# {title}",
        "",
        "Generated by `python -m tools.debugger visualize` for this Pokemon Gold romhack worktree.",
        "",
        f"- Root: `{root}`",
        f"- Reports: {len(reports)}",
        f"- Traces: {len(traces)}",
        f"- Timeline events: {len(timeline)}",
        f"- Workflow steps: {len(waterfall)}",
        f"- Graph: {len(graph['nodes'])} nodes / {len(graph['edges'])} edges",
        f"- Input errors: {len(errors)}",
        "",
    ]
    if errors:
        lines.extend(["## Input Errors", ""])
        lines.extend(f"- {error}" for error in errors)
        lines.append("")
    lines.extend(["## Lane Summary", ""])
    if lane_summary:
        lines.append("| Lane | Count | Max Severity | Sources |")
        lines.append("| --- | ---: | ---: | --- |")
        for lane in lane_summary:
            lines.append(
                f"| {markdown_cell(lane['lane'])} | {lane['count']} | {lane['max_severity']} | "
                f"{markdown_cell(', '.join(lane['sources']))} |"
            )
    else:
        lines.append("No lanes were produced.")
    lines.extend(["", "## Timeline", "", "```mermaid", mermaid_timeline.rstrip(), "```", ""])
    lines.extend(["## Causal Graph", "", "```mermaid", mermaid_graph.rstrip(), "```", ""])
    lines.extend(["## Workflow Waterfall", ""])
    if waterfall:
        for step in waterfall[:40]:
            lines.append(f"- `{step['status']}` {step['phase']}: `{step['title']}`")
            if step.get("detail"):
                lines.append(f"  {step['detail']}")
    else:
        lines.append("No workflow steps were found.")
    lines.extend(["", "## Highest Severity Events", ""])
    for item in sorted(timeline, key=lambda event: -int(event.get("severity", 0)))[:30]:
        lines.append(f"- S{item['severity']} `{item['lane']}/{item['type']}` {item['title']}")
        if item.get("detail"):
            lines.append(f"  {item['detail']}")
    return "\n".join(lines).rstrip() + "\n"


def render_html_visualization(
    *,
    title: str,
    root: Path,
    reports: list[dict[str, Any]],
    traces: list[dict[str, Any]],
    timeline: list[dict[str, Any]],
    waterfall: list[dict[str, Any]],
    graph: dict[str, list[dict[str, Any]]],
    lane_summary: list[dict[str, Any]],
    mermaid_timeline: str,
    mermaid_graph: str,
    errors: list[str],
) -> str:
    inspector = render_html_inspector(
        timeline=timeline,
        waterfall=waterfall,
        graph=graph,
        lane_summary=lane_summary,
    )
    rows = "".join(
        "<tr>"
        f"<td>{escape(lane['lane'])}</td>"
        f"<td>{lane['count']}</td>"
        f"<td>{lane['max_severity']}</td>"
        f"<td>{escape(', '.join(lane['sources']))}</td>"
        "</tr>"
        for lane in lane_summary
    ) or "<tr><td colspan=\"4\">No lanes were produced.</td></tr>"
    events = "".join(
        f"<li><strong>S{item['severity']} {escape(item['lane'])}/{escape(item['type'])}</strong>: "
        f"{escape(item['title'])}<br><span>{escape(item.get('detail', ''))}</span></li>"
        for item in sorted(timeline, key=lambda event: -int(event.get("severity", 0)))[:40]
    )
    steps = "".join(
        f"<li><code>{escape(step['status'])}</code> {escape(step['phase'])}: "
        f"<code>{escape(step['title'])}</code><br><span>{escape(step.get('detail', ''))}</span></li>"
        for step in waterfall[:40]
    )
    return "\n".join(
        [
            "<!doctype html>",
            "<html lang=\"en\">",
            "<head>",
            "<meta charset=\"utf-8\">",
            f"<title>{escape(title)}</title>",
            "<style>",
            "body{font-family:Segoe UI,Arial,sans-serif;margin:32px;line-height:1.45;color:#1f2328;background:#fff}",
            "h1,h2{line-height:1.2}code{background:#f6f8fa;padding:2px 4px;border-radius:4px}",
            "table{border-collapse:collapse;width:100%;margin:12px 0 24px}th,td{border:1px solid #d0d7de;padding:6px 8px;text-align:left;vertical-align:top}",
            "pre{background:#f6f8fa;border:1px solid #d0d7de;padding:12px;overflow:auto}.issue{color:#9a3412}span,.muted{color:#57606a}",
            ".inspector{border:1px solid #d0d7de;padding:16px;margin:24px 0}.controls{display:flex;gap:12px;flex-wrap:wrap}.controls label{font-weight:600}.controls input,.controls select{margin-left:4px}",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>{escape(title)}</h1>",
            "<p>Generated by <code>python -m tools.debugger visualize</code> for this Pokemon Gold romhack worktree.</p>",
            "<ul>",
            f"<li>Root: <code>{escape(str(root))}</code></li>",
            f"<li>Reports: {len(reports)}</li>",
            f"<li>Traces: {len(traces)}</li>",
            f"<li>Timeline events: {len(timeline)}</li>",
            f"<li>Workflow steps: {len(waterfall)}</li>",
            f"<li>Graph: {len(graph['nodes'])} nodes / {len(graph['edges'])} edges</li>",
            f"<li>Input errors: {len(errors)}</li>",
            "</ul>",
            render_html_errors(errors),
            "<h2>Lane Summary</h2>",
            "<table><thead><tr><th>Lane</th><th>Count</th><th>Max Severity</th><th>Sources</th></tr></thead>",
            f"<tbody>{rows}</tbody></table>",
            inspector,
            "<h2>Timeline Mermaid</h2>",
            f"<pre>{escape(mermaid_timeline)}</pre>",
            "<h2>Causal Graph Mermaid</h2>",
            f"<pre>{escape(mermaid_graph)}</pre>",
            "<h2>Workflow Waterfall</h2>",
            f"<ul>{steps or '<li>No workflow steps were found.</li>'}</ul>",
            "<h2>Highest Severity Events</h2>",
            f"<ul>{events or '<li>No timeline events were found.</li>'}</ul>",
            "</body>",
            "</html>",
            "",
        ]
    )


def render_html_inspector(
    *,
    timeline: list[dict[str, Any]],
    waterfall: list[dict[str, Any]],
    graph: dict[str, list[dict[str, Any]]],
    lane_summary: list[dict[str, Any]],
) -> str:
    payload = {
        "timeline": timeline,
        "waterfall": waterfall,
        "graph": graph,
        "lanes": lane_summary,
    }
    data = json.dumps(payload, sort_keys=True).replace("</", "<\\/")
    return "\n".join(
        [
            '<section class="inspector" data-kind="interactive-inspector">',
            "<h2>Interactive Evidence Inspector</h2>",
            '<div class="controls">',
            '<label>Search <input id="evidence-search" type="search" placeholder="symbol, file, command, detail"></label>',
            '<label>Lane <select id="lane-filter"><option value="">All lanes</option></select></label>',
            '<label>Source <select id="source-filter"><option value="">All sources</option></select></label>',
            '<label>Min severity <input id="severity-filter" type="number" min="0" max="100" value="0"></label>',
            "</div>",
            '<div id="inspector-count" class="muted"></div>',
            '<table id="evidence-table"><thead><tr><th>Lane</th><th>Type</th><th>Severity</th><th>Title</th><th>Source</th><th>Detail</th></tr></thead><tbody></tbody></table>',
            '<h3>Graph Edges</h3>',
            '<table id="edge-table"><thead><tr><th>From</th><th>Relation</th><th>To</th><th>Source</th></tr></thead><tbody></tbody></table>',
            f'<script id="debugger-visualization-data" type="application/json">{data}</script>',
            "<script>",
            "(() => {",
            "const data = JSON.parse(document.getElementById('debugger-visualization-data').textContent);",
            "const events = [...data.timeline, ...data.waterfall.map(step => ({lane:'workflow', type:step.status, severity:0, title:step.title, source:step.source, detail:step.detail || step.phase}))];",
            "const lanes = Array.from(new Set(events.map(item => item.lane).filter(Boolean))).sort();",
            "const sources = Array.from(new Set(events.map(item => item.source).filter(Boolean))).sort();",
            "const laneFilter = document.getElementById('lane-filter');",
            "const sourceFilter = document.getElementById('source-filter');",
            "for (const lane of lanes) laneFilter.insertAdjacentHTML('beforeend', `<option value=\"${escapeHtml(lane)}\">${escapeHtml(lane)}</option>`);",
            "for (const source of sources) sourceFilter.insertAdjacentHTML('beforeend', `<option value=\"${escapeHtml(source)}\">${escapeHtml(source)}</option>`);",
            "for (const id of ['evidence-search','lane-filter','source-filter','severity-filter']) document.getElementById(id).addEventListener('input', render);",
            "render();",
            "function render(){",
            "  const query = document.getElementById('evidence-search').value.toLowerCase();",
            "  const lane = laneFilter.value;",
            "  const source = sourceFilter.value;",
            "  const minSeverity = Number(document.getElementById('severity-filter').value || 0);",
            "  const rows = events.filter(item => matches(item, query, lane, source, minSeverity)).slice(0, 250);",
            "  document.querySelector('#evidence-table tbody').innerHTML = rows.map(eventRow).join('') || '<tr><td colspan=\"6\">No matching evidence.</td></tr>';",
            "  document.getElementById('inspector-count').textContent = `${rows.length} matching evidence rows from ${events.length} events`;",
            "  document.querySelector('#edge-table tbody').innerHTML = data.graph.edges.slice(0, 250).map(edgeRow).join('') || '<tr><td colspan=\"4\">No graph edges.</td></tr>';",
            "}",
            "function matches(item, query, lane, source, minSeverity){",
            "  const haystack = [item.lane, item.type, item.title, item.source, item.detail, ...(item.symbols || []), ...(item.files || [])].join(' ').toLowerCase();",
            "  return (!query || haystack.includes(query)) && (!lane || item.lane === lane) && (!source || item.source === source) && Number(item.severity || 0) >= minSeverity;",
            "}",
            "function eventRow(item){ return `<tr><td>${escapeHtml(item.lane || '')}</td><td>${escapeHtml(item.type || '')}</td><td>${Number(item.severity || 0)}</td><td>${escapeHtml(item.title || '')}</td><td>${escapeHtml(item.source || '')}</td><td>${escapeHtml(item.detail || '')}</td></tr>`; }",
            "function edgeRow(edge){ return `<tr><td>${escapeHtml(edge.from || '')}</td><td>${escapeHtml(edge.relation || '')}</td><td>${escapeHtml(edge.to || '')}</td><td>${escapeHtml(edge.source || '')}</td></tr>`; }",
            "function escapeHtml(value){ return String(value).replace(/[&<>\"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',\"'\":'&#39;'}[char])); }",
            "})();",
            "</script>",
            "</section>",
        ]
    )


def write_visualization(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report["content"], encoding="utf-8", newline="\n")


def timeline_event(
    *,
    lane: str,
    event_type: str,
    title: str,
    source: str,
    frame: Any = None,
    order: int = 0,
    detail: str = "",
    symbols: list[str] | None = None,
    files: list[str] | None = None,
    severity: int = 0,
) -> dict[str, Any]:
    return {
        "lane": lane,
        "type": event_type,
        "title": title,
        "source": source,
        "frame": frame,
        "order": int(order),
        "detail": detail,
        "symbols": unique_list([item for item in symbols or [] if item]),
        "files": unique_list([item for item in files or [] if item]),
        "severity": int(severity),
    }


def waterfall_step(*, phase: str, title: str, source: str, status: str, detail: str, order: int) -> dict[str, Any]:
    return {
        "phase": phase,
        "title": title,
        "source": source,
        "status": status,
        "detail": detail,
        "order": int(order),
    }


def inspector_item_count(
    *,
    timeline: list[dict[str, Any]],
    waterfall: list[dict[str, Any]],
    graph: dict[str, list[dict[str, Any]]],
) -> int:
    return len(timeline) + len(waterfall) + len(graph["nodes"]) + len(graph["edges"])


def trace_observations(data: Any) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    walk_trace(data, out=out)
    return out


def walk_trace(data: Any, *, out: list[dict[str, str]]) -> None:
    if isinstance(data, dict):
        symbol = first_string(data, ("full_symbol", "symbol", "pc_label", "watch", "resolved", "query"))
        source_file = first_string(data, ("source_file",))
        rule_id = first_string(data, ("rule_id",))
        if symbol or source_file or rule_id:
            out.append({"symbol": symbol, "source_file": source_file, "rule_id": rule_id})
        for value in data.values():
            walk_trace(value, out=out)
    elif isinstance(data, list):
        for item in data:
            walk_trace(item, out=out)


def add_graph_node(nodes: dict[str, dict[str, Any]], node_id: str, label: str, node_type: str, source: str) -> None:
    if not node_id:
        return
    safe = safe_id(node_id)
    nodes.setdefault(
        safe,
        {
            "id": safe,
            "label": label or node_id,
            "type": node_type or "node",
            "source": source,
        },
    )


def add_graph_edge(edges: dict[tuple[str, str, str], dict[str, Any]], source_id: str, target_id: str, relation: str, source: str) -> None:
    if not source_id or not target_id:
        return
    from_id = safe_id(source_id)
    to_id = safe_id(target_id)
    key = (from_id, to_id, relation)
    edges.setdefault(
        key,
        {
            "from": from_id,
            "to": to_id,
            "relation": relation or "relates",
            "source": source,
        },
    )


def timeline_sort_key(item: dict[str, Any]) -> tuple[Any, ...]:
    frame = item.get("frame")
    frame_sort = int(frame) if isinstance(frame, int) else 10**9
    return (frame_sort, item.get("source", ""), item.get("lane", ""), item.get("order", 0), item.get("title", ""))


def waterfall_sort_key(item: dict[str, Any]) -> tuple[Any, ...]:
    phase_order = {
        "ingest": 0,
        "reproduce": 1,
        "observe": 2,
        "instruction-trace": 3,
        "localize": 4,
        "prove": 5,
        "verify": 6,
        "capability-audit": 7,
        "escalate": 8,
    }
    return (phase_order.get(item.get("phase", ""), 50), item.get("source", ""), item.get("order", 0), item.get("title", ""))


def command_status(command: str) -> str:
    if not command:
        return "planned"
    if "<" in command or ">" in command:
        return "needs-input"
    return "runnable"


def incomplete_capabilities(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        capability
        for capability in dict_items(data.get("capabilities"))
        if str(capability.get("status", "")) != "complete"
    ]


def capability_title(capability: dict[str, Any]) -> str:
    return str(capability.get("title") or capability.get("id") or "<unknown capability>")


def first_gap(capability: dict[str, Any]) -> str:
    return next(iter(string_items(capability.get("gaps"))), "")


def status_counts_text(data: dict[str, Any]) -> str:
    status_counts = data.get("status_counts") if isinstance(data.get("status_counts"), dict) else {}
    if not status_counts:
        return ""
    return "status_counts=" + ",".join(
        f"{name}={count}" for name, count in sorted(status_counts.items())
    )


def next_step_candidates(data: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    recommendation = data.get("recommendation") if isinstance(data.get("recommendation"), dict) else {}
    for candidate in [recommendation, *dict_items(data.get("candidates"))]:
        if not candidate:
            continue
        key = (
            str(candidate.get("symptom_class", "")),
            str(candidate.get("title", "")),
            str(candidate.get("first_command", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(candidate)
    return out


def embedded_next_step_reports(data: dict[str, Any]) -> list[dict[str, Any]]:
    next_step = data.get("symptom_only_next_step")
    if isinstance(next_step, dict) and next_step.get("kind") == "unified_debugger_next_step":
        return [next_step]
    return []


def candidate_title(candidate: dict[str, Any]) -> str:
    return str(candidate.get("title") or candidate.get("symptom_class") or "<next step>")


def next_step_detail(candidate: dict[str, Any]) -> str:
    parts = [
        f"lane={candidate.get('matched_lane', '')}",
        f"class={candidate.get('symptom_class', '')}",
        f"command={candidate.get('first_command', '')}",
        "required=" + "; ".join(string_items(candidate.get("required_inputs"))),
        "source_refs=" + "; ".join(string_items(candidate.get("source_refs"))),
        "evidence_standard=" + "; ".join(string_items(candidate.get("evidence_standard"))),
        "disproof_standard=" + "; ".join(string_items(candidate.get("disproof_standard"))),
        f"regression_gate={candidate.get('regression_gate', '')}",
    ]
    proof_limit = str(candidate.get("proof_limit", ""))
    if proof_limit:
        parts.append(f"Proof limit: {proof_limit}")
    return " ".join(part for part in parts if part and not part.endswith("="))


def first_string(data: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str):
            return value
    return ""


def source_operand_label(operand: dict[str, Any]) -> str:
    kind = str(operand.get("kind", "operand"))
    if kind == "register":
        name = str(operand.get("name", "register"))
        value = str(operand.get("value", ""))
        origin = str(operand.get("origin", ""))
        return " ".join(part for part in (f"register:{name}", value, origin) if part)
    if kind == "memory":
        address = str(operand.get("address", ""))
        origin = str(operand.get("origin", operand.get("symbol", "")))
        return " ".join(part for part in (f"memory:{address}", origin) if part)
    if kind == "immediate":
        return f"immediate:{operand.get('value', '')}"
    return kind


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
        return [nested for item in value for nested in string_items(item)]
    return [str(value)] if value else []


def unique_list(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value)
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def safe_id(value: str) -> str:
    out = []
    for char in str(value):
        out.append(char if char.isalnum() else "_")
    return ("".join(out).strip("_") or "node")[:96]


def mermaid_text(value: str) -> str:
    return " ".join(str(value).replace('"', "'").replace("|", "/").split())[:120]


def markdown_cell(value: str) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def escape(value: str) -> str:
    return html.escape(str(value), quote=True)


def render_html_errors(errors: list[str]) -> str:
    if not errors:
        return ""
    items = "".join(f"<li>{escape(error)}</li>" for error in errors)
    return f"<h2>Input Errors</h2><ul class=\"issue\">{items}</ul>"
