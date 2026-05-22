from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from .address_boundary import (
    reverse_query_address_boundary_addresses,
    reverse_query_address_boundary_blocks_proof,
    reverse_query_address_boundary_evidence,
    reverse_query_address_boundary_fields,
    reverse_query_address_boundary_summary,
)
from .catalog import ROOT
from .causal_graph import bank_state_record_proof_status_by_source
from .coverage import load_traces
from .evidence import (
    PROOF_STATUS_RANK,
    evidence_atoms,
    normalize_optional_proof_status as normalize_proof_status,
    strongest_proof_status as shared_strongest_proof_status,
    weakest_proof_status as shared_weakest_proof_status,
)
from .ranking import (
    bank_state_record_evidence_from_atoms,
    materialized_save_state_delta,
    minimized_state_patch_save_state_delta,
    save_state_delta_evidence,
    trace_index_item_proof_status,
)
from .reporting import load_reports


VISUALIZATION_FORMATS = {"markdown", "html"}
COMPARE_BOUNDARY_EVIDENCE_PREFIXES = (
    "runtime_sink_evidence=",
    "runtime_symbol_evidence=",
    "proof_downgrade_reason=",
    "hardware_proof_statuses=",
    "hardware_proof_boundary=",
)


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
    emulator_frames = collect_emulator_frames(
        loaded_reports=loaded_reports,
        loaded_traces=loaded_traces,
        max_frames=max_items,
    )
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
        emulator_frames=emulator_frames,
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
            emulator_frames=emulator_frames,
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
        "emulator_canvas": bool(emulator_frames),
        "emulator_frame_count": len(emulator_frames),
        "inspector_item_count": inspector_item_count(
            timeline=timeline,
            waterfall=waterfall,
            graph=graph,
            emulator_frames=emulator_frames,
        ),
        "lane_summary": lane_summary,
        "emulator_frames": emulator_frames,
        "timeline": timeline,
        "waterfall": waterfall,
        "graph": graph,
        "mermaid_timeline": mermaid_timeline,
        "mermaid_graph": mermaid_graph,
        "content": content,
        "known_limits": [
            "HTML output includes a self-contained filterable evidence inspector; Markdown output remains static.",
            "HTML output includes a generic canvas inspector for sampled emulator frames, instruction records, PC/register snapshots, and watch values present in supplied reports.",
            "The canvas inspector replays captured evidence; it does not synthesize missing PPU framebuffer state when no screenshots or framebuffers were recorded.",
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
    collect_played_input_timeline(data, source=source, out=out)
    if kind == "unified_debugger_playtest_packet":
        out.append(
            timeline_event(
                lane="playtest",
                event_type="playtest_packet",
                title=str(data.get("symptom") or data.get("packet_id") or "Playtest packet"),
                source=source,
                detail=playtest_packet_detail(data),
                symbols=playtest_packet_symbols(data),
                files=string_items(data.get("changed_files")),
                addresses=string_items(data.get("addresses")),
                severity=64,
            )
        )
    elif kind == "unified_debugger_visual_snapshot":
        lcd = data.get("lcd_state") if isinstance(data.get("lcd_state"), dict) else {}
        runtime_samples = visual_snapshot_has_runtime_samples(data)
        proof = snapshot_report_proof_status(
            data,
            runtime_samples=runtime_samples,
            downgrade_reason="no_visual_runtime_samples",
        )
        out.append(
            timeline_event(
                lane="visual",
                event_type="visual_snapshot",
                title="Visual/UI snapshot",
                source=source,
                detail=(
                    f"executed={data.get('executed')} runtime_samples={runtime_samples} "
                    f"surfaces={data.get('surface_count', 0)} "
                    f"lcd={lcd.get('lcd_enabled', '')} mode={lcd.get('ppu_mode', '')} "
                    f"screen_frames={data.get('screen_frame_count', 0)} framebuffer={data.get('framebuffer', '')}"
                    + snapshot_proof_downgrade_detail(
                        data,
                        runtime_samples=runtime_samples,
                        downgrade_reason="no_visual_runtime_samples",
                    )
                ).strip(),
                addresses=[
                    str(surface.get("address", ""))
                    for surface in dict_items(data.get("surfaces"))
                    if surface.get("address")
                ],
                severity=62,
                proof_status=proof,
            )
        )
    elif kind == "unified_debugger_audio_snapshot":
        audio = data.get("audio_state") if isinstance(data.get("audio_state"), dict) else {}
        sound_buffer = data.get("sound_buffer") if isinstance(data.get("sound_buffer"), dict) else {}
        runtime_samples = audio_snapshot_has_runtime_samples(data)
        proof = snapshot_report_proof_status(
            data,
            runtime_samples=runtime_samples,
            downgrade_reason="no_audio_runtime_samples",
        )
        out.append(
            timeline_event(
                lane="audio",
                event_type="audio_snapshot",
                title="Audio snapshot",
                source=source,
                detail=(
                    f"executed={data.get('executed')} runtime_samples={runtime_samples} "
                    f"registers={data.get('register_count', 0)} "
                    f"audio={audio.get('audio_enabled', '')} mask={audio.get('channel_enable_mask', '')} "
                    f"sound_buffer={sound_buffer.get('sha256', '')}"
                    + snapshot_proof_downgrade_detail(
                        data,
                        runtime_samples=runtime_samples,
                        downgrade_reason="no_audio_runtime_samples",
                    )
                ).strip(),
                addresses=[
                    str(register.get("address", ""))
                    for register in dict_items(data.get("register_details"))
                    if register.get("address")
                ],
                severity=61,
                proof_status=proof,
            )
        )
    elif is_boss_ai_report(data):
        collect_boss_ai_timeline(data, source=source, out=out)
    elif kind == "unified_debugger_hardware_regression_gate":
        for case in dict_items(data.get("cases")):
            if case.get("hardware_passed"):
                continue
            out.append(
                timeline_event(
                    lane="hardware",
                    event_type="hardware_regression_case",
                    title=f"Pan Docs hardware case {case.get('id', '<case>')}",
                    source=source,
                    detail=hardware_regression_case_detail(case),
                    severity=86,
                    proof_status=case.get("proof_status") or "planned_only",
                )
            )
    elif kind == "unified_debugger_watch_report":
        for event in dict_items(data.get("events")):
            proof = watch_event_proof_status(event, report=data)
            out.append(
                timeline_event(
                    lane="runtime",
                    event_type="watch",
                    title=f"{event.get('watch', '<watch>')} {event.get('old_hex', '')}->{event.get('new_hex', '')}",
                    source=source,
                    frame=event.get("frame"),
                    detail=watch_timeline_detail(event),
                    symbols=[
                        symbol_if_not_address(str(event.get("watch", ""))),
                        str(event.get("pc_label", "")),
                    ],
                    addresses=related_addresses(event),
                    severity=70,
                    proof_status=proof,
                )
            )
    elif kind == "unified_debugger_reverse_query":
        for result in dict_items(data.get("results")):
            target = result.get("target") if isinstance(result.get("target"), dict) else {}
            label = str(target.get("label") or target.get("symbol") or result.get("matched_address") or "target")
            validation = result.get("validation") if isinstance(result.get("validation"), dict) else {}
            checkpoint = result.get("checkpoint_validation") if isinstance(result.get("checkpoint_validation"), dict) else {}
            span = result.get("bounded_effect_span_validation") if isinstance(result.get("bounded_effect_span_validation"), dict) else {}
            proof = reverse_query_result_proof_status(result, report=data)
            boundary_summary = reverse_query_address_boundary_summary(result)
            event = timeline_event(
                lane="reverse",
                event_type="reverse_query",
                title=f"Reverse query {label}",
                source=source,
                detail=(
                    f"writer={result.get('last_writer_pc', '')} "
                    f"validation={validation.get('status', '')} "
                    f"checkpoint={checkpoint.get('status', '')} "
                    f"effect_span={span.get('status', '')} "
                    f"routes={len(dict_items(result.get('validation_routes')))} "
                    f"{boundary_summary}"
                ).strip(),
                symbols=string_items(target.get("symbol")),
                addresses=unique_list([
                    *reverse_query_address_boundary_addresses(result),
                    str(target.get("evidence") or ""),
                    str(result.get("matched_address") or ""),
                ]),
                severity=66,
                proof_status=proof,
                evidence_atoms=result.get("evidence_atoms"),
            )
            event.update(reverse_query_address_boundary_fields(result))
            out.append(event)
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
                    addresses=related_addresses(path),
                    severity=int(path.get("score", 0)),
                    proof_status=path.get("proof_status"),
                )
            )
    elif kind == "unified_debugger_causal_graph":
        for path in dict_items(data.get("paths")):
            out.append(
                timeline_event(
                    lane="causal",
                    event_type="causal_graph_path",
                    title=str(path.get("title", "")),
                    source=source,
                    order=path.get("seq") or 0,
                    detail=(
                        f"proof={path.get('proof_status', '')} "
                        f"score={path.get('score', 0)} confidence={path.get('confidence', 0)}"
                    ),
                    symbols=string_items(path.get("related_symbols")),
                    files=string_items(path.get("related_files")),
                    addresses=related_addresses(path),
                    severity=int(path.get("score", 0)),
                    proof_status=path.get("proof_status"),
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
                    addresses=related_addresses(item),
                    severity=72,
                    proof_status=trace_index_item_proof_status(item, data),
                )
            )
    elif kind in {"unified_debugger_taint_report", "unified_debugger_dynamic_taint_report"}:
        for route in trace_synthesis_routes(data):
            out.append(
                timeline_event(
                    lane="causal",
                    event_type="trace_synthesis",
                    title=trace_synthesis_title(route),
                    source=source,
                    detail=trace_synthesis_detail(route),
                    symbols=trace_synthesis_related_symbols(route),
                    addresses=trace_synthesis_related_addresses(route),
                    severity=trace_synthesis_severity(route),
                    proof_status=route.get("proof_status") or "planned_only",
                )
            )
        for path in dict_items(data.get("paths")):
            proof = dynamic_taint_path_proof_status(path)
            out.append(
                timeline_event(
                    lane="causal",
                    event_type="taint_path",
                    title=str(path.get("title", "")),
                    source=source,
                    detail=(
                        f"contributors={len(dict_items(path.get('contributors')))} "
                        f"confidence={path.get('confidence', 0)}"
                    ),
                    symbols=string_items(path.get("related_symbols")),
                    files=string_items(path.get("related_files")),
                    addresses=related_addresses(path),
                    severity=int(path.get("score", 0)),
                    proof_status=proof,
                )
            )
        for attribution in dict_items(data.get("write_attributions")):
            attribution_proof = normalize_proof_status(attribution.get("proof_status")) or "planned_only"
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
                    addresses=related_addresses(attribution),
                    severity=int(attribution.get("score", 0)),
                    proof_status=attribution_proof,
                )
            )
            for provenance in dict_items(attribution.get("register_provenance")):
                provenance_proof = normalize_proof_status(provenance.get("proof_status")) or attribution_proof
                out.append(
                    timeline_event(
                        lane="causal",
                        event_type="register_provenance",
                        title=f"{register_provenance_title(provenance)} feeds {attribution.get('target', '<sink>')}",
                        source=source,
                        order=int_value(provenance.get("seq", attribution.get("seq"))),
                        detail=register_provenance_detail(provenance),
                        symbols=unique_list(
                            [
                                str(attribution.get("target") or ""),
                                str(provenance.get("pc_label") or ""),
                                *string_items(provenance.get("taint")),
                            ]
                        ),
                        files=string_items(attribution.get("related_files")),
                        addresses=related_addresses(attribution),
                        severity=max(64, int(attribution.get("score", 0))),
                        proof_status=provenance_proof,
                    )
                )
    elif kind == "unified_debugger_effect_trace":
        for event in dict_items(data.get("events")):
            for effect in dict_items(event.get("effects")):
                if effect.get("post_value_status") != "mismatch":
                    continue
                out.append(
                    timeline_event(
                        lane="instruction_trace",
                        event_type="effect_post_value_mismatch",
                        title=effect_post_value_title(effect),
                        source=source,
                        order=event.get("seq"),
                        detail=effect_post_value_detail(effect, event),
                        symbols=[str(event.get("pc_label", ""))],
                        addresses=effect_post_value_addresses(effect),
                        severity=86,
                        proof_status=effect_item_proof_status(effect),
                    )
                )
            for effect in dict_items(event.get("effects")):
                if effect.get("access") != "register_write":
                    continue
                out.append(
                    timeline_event(
                        lane="instruction_trace",
                        event_type="effect_register_write",
                        title=effect_register_write_title(effect),
                        source=source,
                        order=event.get("seq"),
                        detail=effect_register_write_detail(effect, event),
                        symbols=[str(event.get("pc_label", ""))],
                        addresses=effect_source_addresses(effect),
                        severity=72 if effect.get("post_register_status") != "mismatch" else 84,
                    )
                )
            for change in dict_items(event.get("unmodeled_observed_changes")):
                out.append(
                    timeline_event(
                        lane="instruction_trace",
                        event_type="effect_unmodeled_observed_change",
                        title=effect_unmodeled_change_title(change),
                        source=source,
                        order=event.get("seq"),
                        detail=effect_unmodeled_change_detail(change, event),
                        symbols=[str(event.get("pc_label", ""))],
                        addresses=effect_unmodeled_change_addresses(change),
                        severity=84,
                    )
                )
            for effect in dict_items(event.get("effects")):
                if effect.get("access") != "unmodeled":
                    continue
                out.append(
                    timeline_event(
                        lane="instruction_trace",
                        event_type="effect_unmodeled_effect",
                        title=effect_unmodeled_effect_title(effect),
                        source=source,
                        order=event.get("seq"),
                        detail=effect_unmodeled_effect_detail(effect, event),
                        symbols=[str(event.get("pc_label", ""))],
                        addresses=[],
                        severity=82,
                    )
                )
            for hit in dict_items(event.get("watch_hits")):
                watch = str(hit.get("watch") or "")
                address = str(hit.get("address") or "")
                access = str(hit.get("access") or "")
                out.append(
                    timeline_event(
                        lane="instruction_trace",
                        event_type="effect_watch_hit",
                        title=f"{watch or '<watch>'} {access} {address}".strip(),
                        source=source,
                        order=event.get("seq"),
                        detail=effect_watch_hit_detail(hit, event),
                        symbols=[symbol_if_not_address(watch), str(event.get("pc_label", ""))],
                        addresses=unique_list([address, str(hit.get("effect_key", "")), str(hit.get("watch_key", ""))]),
                        severity=74 if access == "write" else 60,
                        proof_status=watch_hit_proof_status(hit),
                    )
                )
        for item in dict_items(data.get("side_effect_index"))[:24]:
            kind_label = str(item.get("kind") or "side_effect")
            is_cpu_state = kind_label == "cpu_state" or str(item.get("category", "")) == "cpu"
            out.append(
                timeline_event(
                    lane="runtime" if is_cpu_state else "instruction_trace",
                    event_type="cpu_state_side_effect" if is_cpu_state else "side_effect",
                    title=side_effect_timeline_title(item),
                    source=source,
                    order=item.get("last_seq"),
                    detail=side_effect_timeline_detail(item),
                    symbols=side_effect_timeline_symbols(item),
                    severity=82 if is_cpu_state else 62,
                    proof_status=side_effect_index_proof_status(item),
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
                    detail=impact_detail(item),
                    symbols=string_items(item.get("related_symbols")),
                    files=string_items(item.get("related_files")),
                    addresses=related_addresses(item),
                    severity=int(item.get("impact_score", 0)),
                    proof_status=item.get("proof_status"),
                )
            )
    elif kind == "unified_debugger_ranked_findings":
        for finding in dict_items(data.get("findings")):
            out.append(
                timeline_event(
                    lane="rank",
                    event_type=str(finding.get("type", "finding")),
                    title=str(finding.get("title", "")),
                    source=source,
                    detail=(
                        f"severity={finding.get('severity', 0)} "
                        f"confidence={finding.get('confidence', 0)}"
                    ),
                    symbols=string_items(finding.get("related_symbols")),
                    files=string_items(finding.get("related_files")),
                    addresses=related_addresses(finding),
                    severity=int(finding.get("severity", 0)),
                    proof_status=finding.get("proof_status"),
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
        state_patch_minimization = data.get("state_patch_minimization")
        if isinstance(state_patch_minimization, dict) and state_patch_minimization.get("attempted"):
            out.append(
                timeline_event(
                    lane="minimize",
                    event_type="state_patch_minimization",
                    title="State patch minimization " + ("preserved" if state_patch_minimization.get("preserved") else "failed"),
                    source=source,
                    detail=state_patch_minimization_detail(state_patch_minimization),
                    symbols=state_patch_minimization_related_symbols(state_patch_minimization),
                    files=string_items(state_patch_minimization.get("source_files")),
                    addresses=state_patch_minimization_related_addresses(state_patch_minimization),
                    severity=64 if state_patch_minimization.get("preserved") else 72,
                )
            )
            for route in dict_items(state_patch_minimization.get("semantic_reducer_routes")):
                out.append(
                    timeline_event(
                        lane="minimize",
                        event_type="semantic_reducer_route",
                        title=f"Semantic reducer route: {route.get('id', route.get('surface', 'route'))}",
                        source=source,
                        detail=semantic_reducer_route_detail(route),
                        files=string_items(route.get("source_file")),
                        severity=52,
                    )
                )
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
                    symbols=unique_list(
                        [
                            *string_items(campaign.get("symbols")),
                            *string_items(campaign.get("related_symbols")),
                        ]
                    ),
                    files=string_items(campaign.get("changed_files")),
                    addresses=related_addresses(campaign),
                    severity=62 if is_dynamic_proof_level(campaign.get("proof_level")) else 42,
                )
            )
        for case in dict_items(data.get("fuzz_cases"))[:40]:
            runtime_targets = case.get("runtime_targets") if isinstance(case.get("runtime_targets"), dict) else {}
            detail = unique_list(
                [
                    *string_items(case.get("expectations"))[:2],
                    f"counterexample_source={case.get('counterexample_source')}" if case.get("counterexample_source") else "",
                    f"runtime_route={runtime_targets.get('runtime_route')}" if runtime_targets.get("runtime_route") else "",
                    f"behavioral_probes={case.get('behavioral_probe_count')}" if case.get("behavioral_probe_count") else "",
                ]
            )
            out.append(
                timeline_event(
                    lane="fuzz",
                    event_type=str(case.get("fuzz_type", "case")),
                    title=str(case.get("id", "")),
                    source=source,
                    detail=", ".join(detail),
                    symbols=fuzz_case_runtime_symbols(case),
                    files=fuzz_case_runtime_files(case),
                    addresses=related_addresses(case),
                    severity=45 if is_dynamic_proof_level(case.get("proof_level")) else 30,
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
                    detail=", ".join(compare_timeline_detail(match)),
                    symbols=unique_list(
                        [
                            *string_items(match.get("related_symbols")),
                            *string_items(match.get("observed_runtime_symbols")),
                        ]
                    ),
                    addresses=string_items(match.get("related_addresses")),
                    severity=55 if match.get("gaps") else 35,
                    proof_status=match.get("proof_status"),
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
    proof = instruction_trace_validation_proof_status(data, validation)
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
            proof_status=proof,
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
                proof_status=proof,
                )
            )


def collect_played_input_timeline(data: dict[str, Any], *, source: str, out: list[dict[str, Any]]) -> None:
    for played in dict_items(data.get("played_inputs"))[:120]:
        proof = played_input_proof_status(data, played)
        out.append(
            timeline_event(
                lane="inputs",
                event_type="played_input",
                title=played_input_title(played),
                source=source,
                frame=played.get("frame"),
                detail=played_input_detail(played),
                severity=58,
                proof_status=proof,
            )
        )


def collect_played_input_graph(
    data: dict[str, Any],
    *,
    source: str,
    nodes: dict[str, dict[str, Any]],
    edges: dict[tuple[str, str, str], dict[str, Any]],
) -> None:
    report_id = f"{source}:report"
    add_graph_node(nodes, report_id, source, "report", source)
    for played in dict_items(data.get("played_inputs"))[:200]:
        proof = played_input_proof_status(data, played)
        input_id = played_input_graph_id(source, played)
        add_graph_node(nodes, input_id, played_input_title(played), "played_input", source, proof)
        add_graph_edge(edges, report_id, input_id, "played_input", source, proof)


def played_input_graph_id(source: str, played: dict[str, Any]) -> str:
    buttons = "+".join(string_items(played.get("buttons"))) or "wait"
    return f"{source}:played_input:{played.get('frame', '')}:{played.get('line', '')}:{buttons}"


def collect_effect_trace_graph(
    data: dict[str, Any],
    *,
    source: str,
    nodes: dict[str, dict[str, Any]],
    edges: dict[tuple[str, str, str], dict[str, Any]],
) -> None:
    report_id = f"{source}:effect_trace"
    report_proof = effect_trace_report_graph_proof_status(data)
    report_summary = effect_trace_report_graph_proof_summary(data, report_proof=report_proof)
    report_node = add_graph_node(
        nodes,
        report_id,
        source,
        "effect_trace",
        source,
        report_proof,
        proof_summary=report_summary,
    )
    if report_node is not None:
        attach_effect_trace_report_graph_fields(report_node, data)
    for event in dict_items(data.get("events")):
        pc_label = str(event.get("pc_label") or event.get("pc_bank_address") or "")
        if pc_label:
            pc_id = f"{source}:instruction:{event.get('seq', '')}:{pc_label}"
            add_graph_node(nodes, pc_id, pc_label, "instruction", source, "instruction_observed")
            add_graph_edge(edges, report_id, pc_id, "observed_instruction", source, "instruction_observed")
        else:
            pc_id = report_id
        for effect_index, effect in enumerate(dict_items(event.get("effects"))):
            status = str(effect.get("post_value_status") or "")
            if not status:
                continue
            address = str(effect.get("address_hex") or effect.get("address") or "")
            effect_id = f"{source}:effect:{event.get('seq', '')}:{effect_index}:{address}:{effect.get('operation', '')}"
            validation_id = f"{source}:post_value:{event.get('seq', '')}:{effect_index}:{status}:{address}:{effect.get('post_observed_pc', '')}"
            relation = "post_value_mismatch" if status == "mismatch" else "post_value_confirmed"
            proof = effect_item_proof_status(effect)
            add_graph_node(nodes, effect_id, str(effect.get("operation") or "effect"), "effect", source, proof)
            add_graph_node(nodes, validation_id, effect_post_value_title(effect), "post_value_validation", source, proof)
            add_graph_edge(edges, pc_id, effect_id, "executes_effect", source, proof)
            add_graph_edge(edges, effect_id, validation_id, relation, source, proof)
            if address:
                add_graph_node(nodes, address, address, "address", source, proof)
                add_graph_edge(edges, validation_id, address, "checks_address_value", source, proof)
        for effect_index, effect in enumerate(dict_items(event.get("effects"))):
            if effect.get("access") != "register_write":
                continue
            register = str(effect.get("register") or "")
            effect_id = f"{source}:register_write:{event.get('seq', '')}:{effect_index}:{register}:{effect.get('operation', '')}"
            register_id = f"{source}:register:{register}"
            proof = effect_item_proof_status(effect)
            add_graph_node(nodes, effect_id, effect_register_write_title(effect), "register_write", source, proof)
            add_graph_node(nodes, register_id, register, "register", source, proof)
            add_graph_edge(edges, pc_id, effect_id, "executes_effect", source, proof)
            add_graph_edge(edges, effect_id, register_id, "writes_register", source, proof)
            status = str(effect.get("post_register_status") or "")
            if status:
                validation_id = f"{source}:post_register:{event.get('seq', '')}:{effect_index}:{status}:{register}:{effect.get('post_observed_pc', '')}"
                relation = "post_register_mismatch" if status == "mismatch" else "post_register_confirmed"
                add_graph_node(nodes, validation_id, effect_register_validation_title(effect), "post_register_validation", source, proof)
                add_graph_edge(edges, effect_id, validation_id, relation, source, proof)
                add_graph_edge(edges, validation_id, register_id, "checks_register_value", source, proof)
        for change_index, change in enumerate(dict_items(event.get("unmodeled_observed_changes"))):
            address = str(change.get("address") or "")
            if not address:
                continue
            change_id = f"{source}:unmodeled_observed_change:{event.get('seq', '')}:{change_index}:{address}:{change.get('next_pc', '')}"
            add_graph_node(nodes, change_id, effect_unmodeled_change_title(change), "unmodeled_observed_change", source, "instruction_observed")
            add_graph_edge(edges, pc_id, change_id, "unmodeled_observed_change", source, "instruction_observed")
            add_graph_node(nodes, address, address, "address", source, "instruction_observed")
            add_graph_edge(edges, change_id, address, "changed_unattributed_address", source, "instruction_observed")
        for effect_index, effect in enumerate(dict_items(event.get("effects"))):
            if effect.get("access") != "unmodeled":
                continue
            effect_id = f"{source}:unmodeled_effect:{event.get('seq', '')}:{effect_index}:{effect.get('operation', '')}"
            proof = effect_item_proof_status(effect)
            add_graph_node(nodes, effect_id, effect_unmodeled_effect_title(effect), "unmodeled_effect", source, proof)
            add_graph_edge(edges, pc_id, effect_id, "has_unmodeled_effect", source, proof)


def watch_timeline_detail(event: dict[str, Any]) -> str:
    dynamic_context = event.get("dynamic_context") if isinstance(event.get("dynamic_context"), dict) else {}
    input_context = event.get("input_context") if isinstance(event.get("input_context"), dict) else {}
    last_input = input_context.get("last_input") if isinstance(input_context.get("last_input"), dict) else {}
    parts = [
        str(event.get("pc_bank_address", "")),
        str(event.get("pc_label", "")),
        f"context={dynamic_context.get('context_frame_count', 0)}",
    ]
    if last_input:
        parts.append(f"input={played_input_title(last_input)}")
    return " ".join(part for part in parts if part).strip()


def played_input_title(played: dict[str, Any]) -> str:
    buttons = "+".join(string_items(played.get("buttons")))
    if not buttons:
        return f"wait frame {played.get('frame', '')}"
    return f"input {buttons} frame {played.get('frame', '')}"


def played_input_detail(played: dict[str, Any]) -> str:
    buttons = "+".join(string_items(played.get("buttons")))
    parts = [
        f"frame={played.get('frame')}",
        f"buttons={buttons}" if buttons else "wait=true",
        f"hold={played.get('hold_frames')}" if played.get("hold_frames") else "",
        f"line={played.get('line')}" if played.get("line") else "",
    ]
    return " ".join(part for part in parts if part)


def played_input_proof_status(data: dict[str, Any], played: dict[str, Any]) -> str:
    explicit = normalize_proof_status(played.get("proof_status")) if played.get("proof_status") else ""
    if explicit:
        return explicit
    if data.get("executed") and bool(data.get("valid", True)):
        return "runtime_observed"
    return "planned_only"


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


def playtest_packet_detail(data: dict[str, Any]) -> str:
    parts = [
        f"packet_id={data.get('packet_id', '')}",
        f"artifacts={data.get('artifact_count', 0)}",
        f"routes={data.get('evidence_route_count', 0)}",
        f"save_state={data.get('save_state', '')}",
        f"input_log={data.get('input_log', '')}",
        f"screenshot={data.get('screenshot', '')}",
        f"proof={data.get('proof_status', '')}",
    ]
    return " ".join(part for part in parts if part and not part.endswith("="))


def playtest_packet_symbols(data: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            *string_items(data.get("symbols_to_investigate")),
            *string_items(data.get("watch_symbols")),
        ]
    )


def impact_detail(item: dict[str, Any]) -> str:
    parts = [
        f"impact={item.get('impact_score', 0)}",
        f"surface={item.get('surface', '')}",
    ]
    if item.get("semantic_score") is not None:
        parts.append(f"semantic={item.get('semantic_score', 0)}")
    factors = string_items(item.get("semantic_factors"))
    if factors:
        parts.append("factors=" + "; ".join(factors[:3]))
    return " ".join(part for part in parts if part)


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


def fuzz_case_runtime_symbols(case: dict[str, Any]) -> list[str]:
    runtime_targets = case.get("runtime_targets") if isinstance(case.get("runtime_targets"), dict) else {}
    symbols = [
        *string_items(case.get("symbols")),
        *string_items(case.get("related_symbols")),
    ]
    for key in ("source_symbols", "script_symbols", "trace_symbols", "watch_symbols"):
        symbols.extend(string_items(runtime_targets.get(key)))
    for precondition in dict_items(case.get("state_preconditions")):
        symbols.extend(string_items(precondition.get("watch_symbols")))
    return unique_list(symbols)


def is_dynamic_proof_level(value: Any) -> bool:
    text = str(value)
    return text == "dynamic" or text.startswith("dynamic_") or text.startswith("positioned_state_dynamic")


def fuzz_case_runtime_files(case: dict[str, Any]) -> list[str]:
    runtime_targets = case.get("runtime_targets") if isinstance(case.get("runtime_targets"), dict) else {}
    files = [
        *string_items(case.get("changed_file")),
        *string_items(case.get("source_file")),
        *string_items(case.get("related_files")),
        *string_items(runtime_targets.get("source_files")),
    ]
    for probe in dict_items(case.get("behavioral_probes")):
        files.extend(string_items(probe.get("source_file")))
    return unique_list(files)


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
        delta_evidence = save_state_delta_evidence(materialized_save_state_delta(data))
        detail = " ".join(
            part
            for part in [
                f"applied_patches={len(applied_patches)}",
                ", ".join(content_state_patch_evidence(applied_patches)[:4]),
                *delta_evidence,
            ]
            if part
        )
        out.append(
            timeline_event(
                lane="runtime",
                event_type="content_state_executed",
                title=f"Patched content state saved: {out_state or source}",
                source=source,
                detail=detail,
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
        delta_evidence = save_state_delta_evidence(materialized_save_state_delta(data))
        detail = " ".join(
            part
            for part in [
                f"applied_patches={len(applied_patches)}",
                ", ".join(content_state_patch_evidence(applied_patches)[:4]),
                *delta_evidence,
            ]
            if part
        )
        out.append(
            timeline_event(
                lane="runtime",
                event_type="state_space_executed",
                title=f"Patched state-space saved: {out_state or source}",
                source=source,
                detail=detail,
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
                addresses=[item.get("address", "")],
                severity=30,
            )
        )


def collect_waterfall(*, loaded_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    for loaded in loaded_reports:
        data = loaded["data"]
        source = loaded["source"]
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
        if data.get("kind") in {"unified_debugger_taint_report", "unified_debugger_dynamic_taint_report"}:
            for route in trace_synthesis_routes(data):
                for index, command in enumerate(string_items(route.get("commands"))):
                    steps.append(
                        waterfall_step(
                            phase="trace-synthesis",
                            title=command,
                            source=source,
                            status=command_status(command),
                            detail=trace_synthesis_detail(route),
                            order=index,
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
        collect_played_input_graph(data, source=source, nodes=nodes, edges=edges)
        if kind == "unified_debugger_playtest_packet":
            packet_id = str(data.get("packet_id") or source)
            packet_node = f"{source}:playtest_packet:{packet_id}"
            add_graph_node(nodes, packet_node, str(data.get("symptom") or packet_id), "playtest_packet", source)
            symptom = str(data.get("symptom", ""))
            if symptom:
                add_graph_node(nodes, symptom, symptom, "symptom", source)
                add_graph_edge(edges, packet_node, symptom, "records_symptom", source)
            for artifact_key, artifact_type in (
                ("rom", "rom"),
                ("symbols", "symbols"),
                ("save_state", "save_state"),
                ("input_log", "input_log"),
                ("screenshot", "screenshot"),
            ):
                artifact = str(data.get(artifact_key) or "")
                if artifact:
                    add_graph_node(nodes, artifact, artifact, artifact_type, source)
                    add_graph_edge(edges, packet_node, artifact, f"includes_{artifact_type}", source)
            for path in string_items(data.get("changed_files")):
                add_graph_node(nodes, path, path, "content_source", source)
                add_graph_edge(edges, path, packet_node, "scopes_playtest", source)
            for symbol in playtest_packet_symbols(data):
                add_graph_node(nodes, symbol, symbol, "playtest_symbol", source)
                add_graph_edge(edges, packet_node, symbol, "targets_symbol", source)
            for address in string_items(data.get("addresses")):
                add_graph_node(nodes, address, address, "playtest_address", source)
                add_graph_edge(edges, packet_node, address, "targets_address", source)
            for route in dict_items(data.get("evidence_routes")):
                route_id = f"{source}:playtest_route:{packet_id}:{route.get('id', '')}"
                add_graph_node(
                    nodes,
                    route_id,
                    str(route.get("title") or route.get("id") or "evidence route"),
                    "playtest_route",
                    source,
                    route.get("proof_status") or "planned_only",
                )
                add_graph_edge(edges, packet_node, route_id, "plans_evidence_route", source, "planned_only")
                produced = str(route.get("produces") or "")
                if produced:
                    output_id = f"{source}:planned_output:{produced}"
                    add_graph_node(nodes, output_id, produced, "planned_output", source, "planned_only")
                    add_graph_edge(edges, route_id, output_id, "produces_report", source, "planned_only")
        elif kind == "unified_debugger_visual_snapshot":
            proof = snapshot_report_proof_status(
                data,
                runtime_samples=visual_snapshot_has_runtime_samples(data),
                downgrade_reason="no_visual_runtime_samples",
            )
            snapshot_id = f"{source}:visual_snapshot"
            add_graph_node(nodes, snapshot_id, "Visual/UI snapshot", "visual_snapshot", source, proof)
            for surface in dict_items(data.get("surfaces")):
                name = str(surface.get("name") or surface.get("address") or "surface")
                surface_id = f"{source}:visual_surface:{name}:{surface.get('address', '')}:{surface.get('bank', '')}"
                add_graph_node(nodes, surface_id, name, "visual_surface", source, proof)
                add_graph_edge(edges, snapshot_id, surface_id, "samples_surface", source, proof)
        elif kind == "unified_debugger_audio_snapshot":
            proof = snapshot_report_proof_status(
                data,
                runtime_samples=audio_snapshot_has_runtime_samples(data),
                downgrade_reason="no_audio_runtime_samples",
            )
            snapshot_id = f"{source}:audio_snapshot"
            add_graph_node(nodes, snapshot_id, "Audio snapshot", "audio_snapshot", source, proof)
            for register in dict_items(data.get("register_details")):
                name = str(register.get("name") or register.get("address") or "audio_register")
                register_id = f"{source}:audio_register:{name}:{register.get('address', '')}"
                add_graph_node(nodes, register_id, name, "audio_register", source, proof)
                add_graph_edge(edges, snapshot_id, register_id, "samples_audio_register", source, proof)
            for item in dict_items(data.get("symbol_state")):
                symbol = str(item.get("symbol") or item.get("address") or "audio_symbol")
                symbol_id = f"{source}:audio_symbol_state:{symbol}:{item.get('address', '')}:{item.get('bank', '')}"
                add_graph_node(nodes, symbol_id, symbol, "audio_symbol_state", source, proof)
                add_graph_edge(edges, snapshot_id, symbol_id, "samples_audio_state", source, proof)
            wave = data.get("wave_ram") if isinstance(data.get("wave_ram"), dict) else {}
            if wave:
                wave_id = f"{source}:audio_wave_ram:{wave.get('address', '')}"
                add_graph_node(nodes, wave_id, "Wave RAM", "audio_wave_ram", source, proof)
                add_graph_edge(edges, snapshot_id, wave_id, "samples_audio_wave_ram", source, proof)
            sound_buffer = data.get("sound_buffer") if isinstance(data.get("sound_buffer"), dict) else {}
            if sound_buffer:
                sound_id = f"{source}:audio_sound_buffer:{sound_buffer.get('source', '')}:{sound_buffer.get('sha256', '')}"
                add_graph_node(nodes, sound_id, "PyBoy sound buffer", "audio_sound_buffer", source, proof)
                add_graph_edge(edges, snapshot_id, sound_id, "samples_audio_sound_buffer", source, proof)
        elif kind == "unified_debugger_watch_report":
            for index, event in enumerate(dict_items(data.get("events"))):
                watch_name = str(event.get("watch", ""))
                event_id = f"{source}:watch:{index}:{watch_name}"
                pc_label = str(event.get("pc_label", ""))
                proof = watch_event_proof_status(event, report=data)
                add_graph_node(nodes, event_id, watch_name or "watch event", "watch_event", source, proof)
                add_graph_node(nodes, pc_label, pc_label, "instruction", source, proof)
                add_graph_edge(edges, pc_label, event_id, "writes", source, proof)
                input_context = event.get("input_context") if isinstance(event.get("input_context"), dict) else {}
                for played in dict_items(input_context.get("played_inputs")):
                    input_id = played_input_graph_id(source, played)
                    add_graph_node(nodes, input_id, played_input_title(played), "played_input", source, "runtime_observed")
                    add_graph_edge(edges, input_id, event_id, "precedes_observed_change", source, "runtime_observed")
                symbol = symbol_if_not_address(watch_name)
                if symbol:
                    add_graph_node(nodes, symbol, symbol, "watch_symbol", source, proof)
                    add_graph_edge(edges, event_id, symbol, "observes", source, proof)
                for address in related_addresses(event):
                    add_graph_node(nodes, address, address, "watch_address", source, proof)
                    add_graph_edge(edges, event_id, address, "observes_address", source, proof)
        elif kind == "unified_debugger_effect_trace":
            collect_effect_trace_graph(data, source=source, nodes=nodes, edges=edges)
        elif kind == "unified_debugger_hardware_regression_gate":
            collect_hardware_regression_graph(data, source=source, nodes=nodes, edges=edges)
        elif kind == "unified_debugger_reverse_query":
            for result in dict_items(data.get("results")):
                target = result.get("target") if isinstance(result.get("target"), dict) else {}
                label = str(target.get("label") or target.get("symbol") or result.get("matched_address") or "target")
                query_id = f"{source}:reverse_query:{label}:{result.get('last_writer_seq', '')}"
                result_proof = reverse_query_result_proof_status(result, report=data)
                address_boundary_fields = reverse_query_address_boundary_fields(result)
                address_boundary_evidence = reverse_query_address_boundary_evidence(result)
                query_node = add_graph_node(
                    nodes,
                    query_id,
                    f"Reverse query {label}",
                    "reverse_query",
                    source,
                    result_proof,
                    evidence_atoms=result.get("evidence_atoms"),
                )
                if query_node is not None:
                    query_node.update(address_boundary_fields)
                    query_node["addresses"] = unique_list(
                        [
                            *string_items(query_node.get("addresses")),
                            *reverse_query_address_boundary_addresses(result),
                        ]
                    )
                    query_node["evidence"] = unique_list(
                        [*string_items(query_node.get("evidence")), *address_boundary_evidence]
                    )
                collect_reverse_query_address_boundary_graph(
                    result,
                    source=source,
                    label=label,
                    query_id=query_id,
                    query_proof=result_proof,
                    nodes=nodes,
                    edges=edges,
                )
                checkpoint = result.get("checkpoint_validation") if isinstance(result.get("checkpoint_validation"), dict) else {}
                if checkpoint.get("checkpointed"):
                    checkpoint_data = checkpoint.get("checkpoint") if isinstance(checkpoint.get("checkpoint"), dict) else {}
                    checkpoint_id = f"{source}:trace_checkpoint:{label}:{checkpoint_data.get('source', '')}:{checkpoint_data.get('seq', '')}"
                    checkpoint_proof = checkpoint.get("proof_status") or result_proof
                    add_graph_node(nodes, checkpoint_id, f"Trace checkpoint seq {checkpoint_data.get('seq', '')}", "trace_checkpoint", source, checkpoint_proof)
                    add_graph_edge(edges, checkpoint_id, query_id, "bounds_effect_span", source, checkpoint_proof)
                span = result.get("bounded_effect_span_validation") if isinstance(result.get("bounded_effect_span_validation"), dict) else {}
                if span:
                    span_id = f"{source}:bounded_effect_span:{label}:{span.get('from_seq', '')}:{span.get('to_seq', '')}:{span.get('status', '')}"
                    span_proof = span.get("proof_status") or "planned_only"
                    add_graph_node(nodes, span_id, f"Bounded effect span {span.get('status', '')}", "bounded_effect_span", source, span_proof)
                    add_graph_edge(edges, span_id, query_id, "checks_effect_span", source, span_proof)
                for route in dict_items(result.get("validation_routes")):
                    route_id = f"{source}:reverse_validation_route:{label}:{route.get('id', '')}"
                    route_proof = route.get("proof_status") or "planned_only"
                    add_graph_node(nodes, route_id, str(route.get("title") or route.get("id") or "validation route"), "reverse_validation_route", source, route_proof)
                    add_graph_edge(edges, query_id, route_id, "validates_answer", source, route_proof)
                    produced = str(route.get("produces") or "")
                    if produced:
                        output_id = f"{source}:planned_output:{produced}"
                        add_graph_node(nodes, output_id, produced, "planned_output", source)
                        add_graph_edge(edges, route_id, output_id, "produces_report", source, "planned_only")
        elif kind == "unified_debugger_causal_explanation":
            for path in dict_items(data.get("paths")):
                path_proof = path.get("proof_status")
                for item in dict_items(path.get("nodes")):
                    add_graph_node(nodes, item.get("id", ""), item.get("label", ""), item.get("type", ""), source, item.get("proof_status") or path_proof)
                for edge in dict_items(path.get("edges")):
                    add_graph_edge(edges, edge.get("from", ""), edge.get("to", ""), edge.get("relation", ""), source, edge.get("proof_status") or path_proof)
        elif kind == "unified_debugger_causal_graph":
            for item in dict_items(data.get("nodes")):
                add_graph_node(
                    nodes,
                    str(item.get("id", "")),
                    str(item.get("label", "")),
                    str(item.get("kind", "causal_node")),
                    source,
                    item.get("proof_status"),
                    proof_status_by_source=item.get("proof_status_by_source"),
                    proof_summary=item.get("proof_summary"),
                )
            for edge in dict_items(data.get("edges")):
                add_graph_edge(
                    edges,
                    str(edge.get("from", "")),
                    str(edge.get("to", "")),
                    str(edge.get("relation", "")),
                    source,
                    edge.get("proof_status"),
                )
        elif is_boss_ai_report(data):
            collect_boss_ai_graph(data, source=source, nodes=nodes, edges=edges)
        elif kind == "unified_debugger_causal_slice":
            for target in dict_items(data.get("targets")):
                target_name = str(target.get("resolved") or target.get("query") or "")
                add_graph_node(nodes, target_name, target_name, "symbol", source)
                for edge in [*dict_items(target.get("incoming")), *dict_items(target.get("outgoing"))]:
                    add_graph_node(nodes, str(edge.get("source", "")), str(edge.get("source", "")), "symbol", source)
                    add_graph_node(nodes, str(edge.get("target", "")), str(edge.get("target", "")), "symbol", source)
                    add_graph_edge(edges, str(edge.get("source", "")), str(edge.get("target", "")), str(edge.get("access", "")), source)
        elif kind in {"unified_debugger_taint_report", "unified_debugger_dynamic_taint_report"}:
            for route in trace_synthesis_routes(data):
                proof = normalize_proof_status(route.get("proof_status")) or "planned_only"
                route_id = str(route.get("id") or f"{source}:trace_synthesis:{route.get('match_id', '')}")
                add_graph_node(nodes, route_id, trace_synthesis_title(route), "trace_synthesis", source, proof)
                trace_output = str(route.get("trace_output", ""))
                if trace_output:
                    add_graph_node(nodes, trace_output, trace_output, "instruction_trace_output", source, proof)
                    add_graph_edge(edges, route_id, trace_output, "plans_trace", source, proof)
                save_state = str(route.get("save_state", ""))
                if save_state:
                    add_graph_node(nodes, save_state, save_state, "save_state", source, proof)
                    add_graph_edge(edges, save_state, route_id, "loads_state", source, proof)
                for symbol in string_items(route.get("sink_symbols")):
                    add_graph_node(nodes, symbol, symbol, "dynamic_taint_sink", source, proof)
                    add_graph_edge(edges, route_id, symbol, "watches", source, proof)
                for address in string_items(route.get("sink_addresses")):
                    add_graph_node(nodes, address, address, "dynamic_taint_sink_address", source, proof)
                    add_graph_edge(edges, route_id, address, "watches_address", source, proof)
                for symbol in string_items(route.get("source_symbols")):
                    add_graph_node(nodes, symbol, symbol, "dynamic_taint_source", source, proof)
                    add_graph_edge(edges, symbol, route_id, "seeds_trace", source, proof)
                for address, origin in source_mem_parts(route):
                    if origin:
                        add_graph_node(nodes, origin, origin, "dynamic_taint_source", source, proof)
                        add_graph_edge(edges, origin, route_id, "seeds_trace", source, proof)
                    if address:
                        add_graph_node(nodes, address, address, "dynamic_taint_source_address", source, proof)
                        add_graph_edge(edges, address, route_id, "seeds_memory", source, proof)
                        if origin:
                            add_graph_edge(edges, origin, address, "labels_memory", source, proof)
                for index, command in enumerate(string_items(route.get("commands"))[:6]):
                    command_id = f"{route_id}:command:{index}"
                    add_graph_node(nodes, command_id, command, "workflow_command", source, proof)
                    add_graph_edge(edges, route_id, command_id, "runs", source, proof)
            for path in dict_items(data.get("paths")):
                proof = dynamic_taint_path_proof_status(path)
                target = str(path.get("target", ""))
                add_graph_node(nodes, target, target, "taint_target", source, proof)
                for contributor in dict_items(path.get("contributors")):
                    symbol = str(contributor.get("symbol", ""))
                    add_graph_node(nodes, symbol, symbol, "taint_source", source, proof)
                    add_graph_edge(edges, symbol, target, str(contributor.get("relation", "taints")), source, proof)
                add_related_evidence_graph(nodes, edges, target, path, source=source)
            for attribution in dict_items(data.get("write_attributions")):
                attribution_proof = normalize_proof_status(attribution.get("proof_status")) or "planned_only"
                target = str(attribution.get("target", ""))
                pc_label = str(attribution.get("pc_label", ""))
                write_id = str(attribution.get("id") or f"{target}:{pc_label}:{attribution.get('seq', '')}")
                add_graph_node(nodes, target, target, "dynamic_write_target", source, attribution_proof)
                add_graph_node(nodes, pc_label, pc_label, "instruction", source, attribution_proof)
                add_graph_node(nodes, write_id, str(attribution.get("mnemonic", write_id)), "dynamic_write", source, attribution_proof)
                add_graph_edge(edges, pc_label, write_id, "executes", source, attribution_proof)
                add_graph_edge(edges, write_id, target, "writes", source, attribution_proof)
                for operand in dict_items(attribution.get("source_operands")):
                    operand_label = source_operand_label(operand)
                    add_graph_node(nodes, operand_label, operand_label, "write_operand", source, attribution_proof)
                    add_graph_edge(edges, operand_label, write_id, "feeds", source, attribution_proof)
                    operand_provenance = operand.get("register_provenance") if isinstance(operand.get("register_provenance"), dict) else {}
                    if operand_provenance:
                        operand_provenance_proof = (
                            normalize_proof_status(operand_provenance.get("proof_status")) or attribution_proof
                        )
                        provenance_id = register_provenance_id(operand_provenance)
                        add_graph_node(nodes, provenance_id, register_provenance_title(operand_provenance), "dynamic_register_provenance", source, operand_provenance_proof)
                        add_graph_edge(edges, provenance_id, operand_label, "explains_register_operand", source, operand_provenance_proof)
                    via_register = str(operand.get("via_register", ""))
                    if via_register:
                        provenance = register_provenance_for_operand(operand, attribution)
                        provenance_proof = normalize_proof_status(provenance.get("proof_status")) or attribution_proof
                        provenance_id = register_provenance_id(provenance)
                        add_graph_node(nodes, provenance_id, register_provenance_title(provenance), "dynamic_register_provenance", source, provenance_proof)
                        add_graph_edge(edges, operand_label, provenance_id, "feeds_register", source, dynamic_taint_edge_proof_status(provenance_proof, has_taint=bool(operand.get("origin") or operand.get("symbol"))))
                for provenance in dict_items(attribution.get("register_provenance")):
                    provenance_proof = normalize_proof_status(provenance.get("proof_status")) or attribution_proof
                    provenance_id = register_provenance_id(provenance)
                    register = str(provenance.get("register", ""))
                    register_id = f"register:{register}" if register else ""
                    add_graph_node(nodes, provenance_id, register_provenance_title(provenance), "dynamic_register_provenance", source, provenance_proof)
                    if register_id:
                        add_graph_node(nodes, register_id, register_id, "dynamic_register", source, provenance_proof)
                        add_graph_edge(edges, provenance_id, register_id, "defines_register", source, provenance_proof)
                        add_graph_edge(edges, register_id, write_id, "register_feeds_write", source, attribution_proof)
                    pc = str(provenance.get("pc_label", ""))
                    if pc:
                        add_graph_node(nodes, pc, pc, "instruction", source, provenance_proof)
                        add_graph_edge(edges, pc, provenance_id, "writes_register", source, provenance_proof)
                    add_graph_edge(edges, provenance_id, write_id, "register_feeds_write", source, attribution_proof)
                    for taint in string_items(provenance.get("taint")):
                        taint_proof = dynamic_taint_edge_proof_status(attribution_proof, has_taint=True)
                        add_graph_node(nodes, taint, taint, "dynamic_taint_source", source, taint_proof)
                        add_graph_edge(edges, taint, provenance_id, "taints_register", source, taint_proof)
                add_related_evidence_graph(nodes, edges, write_id, attribution, source=source)
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
                add_related_evidence_graph(nodes, edges, target_id, target, source=source)
        elif kind == "unified_debugger_impact_report":
            for index, item in enumerate(dict_items(data.get("items"))):
                item_id = str(item.get("id") or f"{source}:impact:{index}:{item.get('type', 'impact')}")
                title = str(item.get("title") or item_id)
                add_graph_node(nodes, item_id, title, str(item.get("type", "impact")), source)
                add_related_evidence_graph(nodes, edges, item_id, item, source=source)
        elif kind == "unified_debugger_ranked_findings":
            for index, finding in enumerate(dict_items(data.get("findings"))):
                finding_id = str(finding.get("id") or f"{source}:finding:{index}:{finding.get('type', 'finding')}")
                title = str(finding.get("title") or finding_id)
                add_graph_node(nodes, finding_id, title, "ranked_finding", source)
                add_related_evidence_graph(nodes, edges, finding_id, finding, source=source)
        elif kind == "unified_debugger_fuzz_plan":
            for case in dict_items(data.get("fuzz_cases"))[:40]:
                case_id = str(case.get("id", "fuzz_case"))
                title = str(case.get("fuzz_type") or case_id)
                add_graph_node(nodes, case_id, title, "fuzz_case", source)
                for path in fuzz_case_runtime_files(case):
                    add_graph_node(nodes, path, path, "content_source", source)
                    add_graph_edge(edges, path, case_id, "fuzzes", source)
                runtime_targets = case.get("runtime_targets") if isinstance(case.get("runtime_targets"), dict) else {}
                for symbol in string_items(runtime_targets.get("trace_symbols")):
                    add_graph_node(nodes, symbol, symbol, "runtime_helper", source)
                    add_graph_edge(edges, case_id, symbol, "trace_probe", source)
                for symbol in string_items(runtime_targets.get("watch_symbols")):
                    add_graph_node(nodes, symbol, symbol, "runtime_watch", source)
                    add_graph_edge(edges, case_id, symbol, "watch_probe", source)
                for symbol in fuzz_case_runtime_symbols(case):
                    add_graph_node(nodes, symbol, symbol, "fuzz_symbol", source)
                    add_graph_edge(edges, case_id, symbol, "targets_symbol", source)
                for address in related_addresses(case):
                    add_graph_node(nodes, address, address, "related_address", source)
                    add_graph_edge(edges, case_id, address, "targets_address", source)
                for probe in dict_items(case.get("behavioral_probes")):
                    probe_id = f"{case_id}:{probe.get('id', 'probe')}"
                    add_graph_node(nodes, probe_id, str(probe.get("phase", probe_id)), "behavioral_probe", source)
                    add_graph_edge(edges, case_id, probe_id, str(probe.get("proof_level", "probes")), source)
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
        elif kind == "unified_debugger_minimization_plan":
            collect_minimization_graph(data, source=source, nodes=nodes, edges=edges)
    return {
        "nodes": sorted(nodes.values(), key=lambda item: (item["type"], item["label"])),
        "edges": sorted(edges.values(), key=lambda item: (item["from"], item["to"], item["relation"])),
    }


def collect_minimization_graph(
    data: dict[str, Any],
    *,
    source: str,
    nodes: dict[str, dict[str, Any]],
    edges: dict[tuple[str, str, str], dict[str, Any]],
) -> None:
    state_patch_minimization = data.get("state_patch_minimization")
    if not isinstance(state_patch_minimization, dict) or not state_patch_minimization.get("attempted"):
        return
    route_id = f"{source}:state_patch_minimization"
    add_graph_node(nodes, route_id, "State patch minimization", "minimization_route", source)
    add_related_evidence_graph(nodes, edges, route_id, {
        "related_symbols": state_patch_minimization_related_symbols(state_patch_minimization),
        "related_files": string_items(state_patch_minimization.get("source_files")),
        "related_addresses": state_patch_minimization_related_addresses(state_patch_minimization),
    }, source=source)
    out_report = str(state_patch_minimization.get("out_report", ""))
    if out_report:
        add_graph_node(nodes, out_report, out_report, "minimized_report", source)
        add_graph_edge(edges, route_id, out_report, "writes", source)
    for index, reducer in enumerate(dict_items(state_patch_minimization.get("semantic_reducer_routes"))[:16]):
        reducer_id = f"{route_id}:semantic_reducer:{index}"
        reducer_label = str(reducer.get("id") or reducer.get("surface") or "semantic reducer")
        add_graph_node(nodes, reducer_id, reducer_label, "semantic_reducer_route", source)
        add_graph_edge(edges, route_id, reducer_id, "routes_to_semantic_reducer", source)
        source_file = str(reducer.get("source_file", ""))
        if source_file:
            add_graph_node(nodes, source_file, source_file, "content_source", source)
            add_graph_edge(edges, source_file, reducer_id, "scopes_reducer", source)
        for command_index, command in enumerate(string_items(reducer.get("commands"))[:4]):
            command_id = f"{reducer_id}:command:{command_index}"
            add_graph_node(nodes, command_id, command, "workflow_command", source)
            add_graph_edge(edges, reducer_id, command_id, "runs", source)
    for index, command in enumerate(state_patch_minimization_commands(state_patch_minimization, source=source)[:8]):
        command_id = f"{route_id}:command:{index}"
        add_graph_node(nodes, command_id, command, "workflow_command", source)
        add_graph_edge(edges, route_id, command_id, "runs", source)


def state_patch_minimization_commands(item: dict[str, Any], *, source: str) -> list[str]:
    commands = []
    if source:
        commands.extend(
            [
                f"python -m tools.debugger provenance --report {source}",
                f"python -m tools.debugger taint --report {source}",
                f"python -m tools.debugger slice --report {source}",
            ]
        )
    commands.extend(string_items(item.get("commands")))
    return unique_list(commands)


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
    proof = instruction_trace_validation_proof_status(data, validation)
    validation_id = f"{source}:instruction_trace_validation"
    add_graph_node(nodes, validation_id, str(status["title"]), "instruction_trace_validation", source, proof)
    trace_path = instruction_trace_output_path(data)
    if trace_path:
        trace_output = data.get("trace_output") if isinstance(data.get("trace_output"), dict) else {}
        add_graph_node(nodes, trace_path, trace_path, "instruction_trace_output", source, proof)
        relation = "writes_trace" if trace_output.get("written") else "plans_trace"
        add_graph_edge(edges, validation_id, trace_path, relation, source, proof)
    save_state = instruction_trace_save_state(data)
    if save_state:
        add_graph_node(nodes, save_state, save_state, "save_state", source, proof)
        add_graph_edge(edges, save_state, validation_id, "loads_state", source, proof)
    for symbol in string_items(validation.get("hit_function_symbols")):
        add_graph_node(nodes, symbol, symbol, "instruction_hit", source, proof)
        add_graph_edge(edges, symbol, validation_id, "hit", source, proof)
    for symbol in string_items(validation.get("missing_function_symbols")):
        add_graph_node(nodes, symbol, symbol, "instruction_miss", source, proof)
        add_graph_edge(edges, symbol, validation_id, "missed", source, proof)
    for symbol in string_items(validation.get("watch_symbols")):
        add_graph_node(nodes, symbol, symbol, "watch", source, proof)
        add_graph_edge(edges, validation_id, symbol, "observes", source, proof)


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
        lines.append(f'  {item["id"]}["{mermaid_text(graph_node_mermaid_label(item))}"]')
    for edge in graph["edges"][:120]:
        if edge["from"] not in node_ids or edge["to"] not in node_ids:
            continue
        relation = str(edge.get("relation") or "relates")
        proof = str(edge.get("proof_status") or "")
        label = f"{relation} ({proof})" if proof else relation
        lines.append(f'  {edge["from"]} -->|{mermaid_text(label)}| {edge["to"]}')
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
    emulator_frames: list[dict[str, Any]],
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
        f"- Emulator frames: {len(emulator_frames)}",
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
    lines.extend(["", "## Emulator Frame Samples", ""])
    if emulator_frames:
        lines.append("| Frame | PC | Source | Watches | Registers |")
        lines.append("| ---: | --- | --- | --- | --- |")
        for frame in emulator_frames[:20]:
            watches = ", ".join(
                f"{key}={value}"
                for key, value in dict_items_from_mapping(frame.get("watch_values")).items()
            )
            registers = ", ".join(
                f"{key.upper()}={value}"
                for key, value in dict_items_from_mapping(frame.get("registers")).items()
            )
            pc = " ".join(
                part
                for part in (
                    str(frame.get("pc_bank_address") or ""),
                    str(frame.get("pc_label") or ""),
                )
                if part
            )
            lines.append(
                f"| {markdown_cell(str(frame.get('frame', '')))} | "
                f"{markdown_cell(pc)} | "
                f"{markdown_cell(str(frame.get('source', '')))} | "
                f"{markdown_cell(watches)} | "
                f"{markdown_cell(registers)} |"
            )
    else:
        lines.append("No sampled emulator frames were found in the supplied inputs.")
    lines.extend(["", "## Timeline", "", "```mermaid", mermaid_timeline.rstrip(), "```", ""])
    lines.extend(["## Causal Graph", "", "```mermaid", mermaid_graph.rstrip(), "```", ""])
    mixed_nodes = mixed_proof_nodes(graph)
    if mixed_nodes:
        lines.extend(["## Mixed Proof Nodes", ""])
        lines.append("| Node | Proof Min | Proof Max | Sources |")
        lines.append("| --- | --- | --- | --- |")
        for node in mixed_nodes[:30]:
            source_proofs = node.get("proof_status_by_source") if isinstance(node.get("proof_status_by_source"), dict) else {}
            sources = ", ".join(
                f"{key}={value}"
                for key, value in sorted(source_proofs.items())
            )
            lines.append(
                f"| {markdown_cell(str(node.get('label', '')))} | "
                f"{markdown_cell('proof_min=' + str(node.get('proof_min', '')))} | "
                f"{markdown_cell('proof_max=' + str(node.get('proof_max', '')))} | "
                f"{markdown_cell(sources)} |"
            )
        lines.append("")
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
        if item.get("addresses"):
            lines.append(f"  addresses: {', '.join(f'`{address}`' for address in item['addresses'])}")
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
    emulator_frames: list[dict[str, Any]],
    mermaid_timeline: str,
    mermaid_graph: str,
    errors: list[str],
) -> str:
    canvas_inspector = render_html_canvas_inspector(emulator_frames)
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
        f"{escape(item['title'])}<br><span>{escape(event_detail(item))}</span></li>"
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
            ".canvas-inspector{border:1px solid #d0d7de;padding:16px;margin:24px 0}.canvas-wrap{overflow:auto;border:1px solid #d0d7de;background:#f6f8fa}.canvas-inspector canvas{display:block;max-width:100%}",
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
            canvas_inspector,
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


def render_html_canvas_inspector(emulator_frames: list[dict[str, Any]]) -> str:
    data = json.dumps(emulator_frames, sort_keys=True).replace("</", "<\\/")
    options = "".join(
        f"<option value=\"{index}\">"
        f"{escape(str(frame.get('frame', index)))} {escape(str(frame.get('pc_label') or frame.get('pc_bank_address') or frame.get('kind', 'frame')))}"
        "</option>"
        for index, frame in enumerate(emulator_frames)
    )
    return "\n".join(
        [
            '<section class="canvas-inspector" data-kind="emulator-canvas-inspector">',
            "<h2>Emulator Frame Canvas Inspector</h2>",
            (
                "<p class=\"muted\">Replay sampled emulator evidence from watch, replay, "
                "instruction-trace, and raw trace reports. The canvas shows the captured PC, "
                "registers, watched values, and framebuffer or screenshot references when present.</p>"
            ),
            '<label>Frame <select id="emulator-frame-select">'
            + (options or '<option value="">No sampled frames</option>')
            + "</select></label>",
            '<div class="canvas-wrap"><canvas id="emulator-frame-canvas" width="960" height="420"></canvas></div>',
            '<pre id="emulator-frame-json"></pre>',
            f'<script id="debugger-emulator-frame-data" type="application/json">{data}</script>',
            "<script>",
            "(() => {",
            "const frames = JSON.parse(document.getElementById('debugger-emulator-frame-data').textContent);",
            "const select = document.getElementById('emulator-frame-select');",
            "const canvas = document.getElementById('emulator-frame-canvas');",
            "const ctx = canvas.getContext('2d');",
            "select.addEventListener('input', draw);",
            "draw();",
            "function draw(){",
            "  const frame = frames[Number(select.value || 0)] || null;",
            "  ctx.clearRect(0, 0, canvas.width, canvas.height);",
            "  ctx.fillStyle = '#f6f8fa'; ctx.fillRect(0, 0, canvas.width, canvas.height);",
            "  ctx.fillStyle = '#1f2328'; ctx.font = '16px Consolas, monospace';",
            "  if (!frame) { ctx.fillText('No sampled emulator frames found in these inputs.', 24, 44); document.getElementById('emulator-frame-json').textContent = ''; return; }",
            "  const lines = frameLines(frame);",
            "  ctx.fillStyle = '#0969da'; ctx.fillRect(0, 0, canvas.width, 48);",
            "  ctx.fillStyle = '#ffffff'; ctx.font = '18px Consolas, monospace'; ctx.fillText(lines.shift(), 24, 31);",
            "  ctx.fillStyle = '#1f2328'; ctx.font = '15px Consolas, monospace';",
            "  let y = 78;",
            "  for (const line of lines) { ctx.fillText(line, 24, y); y += 24; }",
            "  drawByteGrid(frame.watch_values || {}, 520, 82, 'Watch values');",
            "  document.getElementById('emulator-frame-json').textContent = JSON.stringify(frame, null, 2);",
            "}",
            "function frameLines(frame){",
            "  const regs = frame.registers || {};",
            "  return [",
            "    `frame=${frame.frame ?? ''} pc=${frame.pc_bank_address || frame.pc_label || ''} source=${frame.source || ''}`,",
            "    `kind=${frame.kind || ''} event=${frame.event_type || ''}`,",
            "    `label=${frame.pc_label || ''}`,",
            "    `registers: ${Object.entries(regs).map(([k,v]) => `${k.toUpperCase()}=${v}`).join('  ') || '<none>'}`,",
            "    `image=${frame.image || frame.framebuffer || '<none>'}`,",
            "    `detail=${frame.detail || ''}`",
            "  ];",
            "}",
            "function drawByteGrid(values, x, y, title){",
            "  ctx.fillStyle = '#57606a'; ctx.fillText(title, x, y - 18);",
            "  const entries = Object.entries(values);",
            "  if (!entries.length) { ctx.fillText('<no watch values>', x, y + 6); return; }",
            "  let row = 0;",
            "  for (const [name, value] of entries.slice(0, 12)) {",
            "    ctx.fillStyle = '#dbeafe'; ctx.fillRect(x, y + row * 28 - 16, 380, 22);",
            "    ctx.fillStyle = '#1f2328'; ctx.fillText(`${name}: ${value}`, x + 8, y + row * 28);",
            "    row += 1;",
            "  }",
            "}",
            "})();",
            "</script>",
            "</section>",
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
            '<table id="evidence-table"><thead><tr><th>Lane</th><th>Type</th><th>Severity</th><th>Title</th><th>Source</th><th>Addresses</th><th>Detail</th></tr></thead><tbody></tbody></table>',
            '<h3>Graph Nodes</h3>',
            '<table id="node-table"><thead><tr><th>Node</th><th>Type</th><th>Proof</th><th>Proof Range</th><th>Sources</th></tr></thead><tbody></tbody></table>',
            '<h3>Graph Edges</h3>',
            '<table id="edge-table"><thead><tr><th>From</th><th>Relation</th><th>Proof</th><th>To</th><th>Source</th></tr></thead><tbody></tbody></table>',
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
            "  document.querySelector('#evidence-table tbody').innerHTML = rows.map(eventRow).join('') || '<tr><td colspan=\"7\">No matching evidence.</td></tr>';",
            "  document.getElementById('inspector-count').textContent = `${rows.length} matching evidence rows from ${events.length} events`;",
            "  document.querySelector('#node-table tbody').innerHTML = data.graph.nodes.slice(0, 250).map(nodeRow).join('') || '<tr><td colspan=\"5\">No graph nodes.</td></tr>';",
            "  document.querySelector('#edge-table tbody').innerHTML = data.graph.edges.slice(0, 250).map(edgeRow).join('') || '<tr><td colspan=\"5\">No graph edges.</td></tr>';",
            "}",
            "function matches(item, query, lane, source, minSeverity){",
            "  const haystack = [item.lane, item.type, item.title, item.source, item.detail, ...(item.symbols || []), ...(item.files || []), ...(item.addresses || [])].join(' ').toLowerCase();",
            "  return (!query || haystack.includes(query)) && (!lane || item.lane === lane) && (!source || item.source === source) && Number(item.severity || 0) >= minSeverity;",
            "}",
            "function eventRow(item){ return `<tr><td>${escapeHtml(item.lane || '')}</td><td>${escapeHtml(item.type || '')}</td><td>${Number(item.severity || 0)}</td><td>${escapeHtml(item.title || '')}</td><td>${escapeHtml(item.source || '')}</td><td>${escapeHtml((item.addresses || []).join(', '))}</td><td>${escapeHtml(item.detail || '')}</td></tr>`; }",
            "function nodeRow(node){ const range = [node.proof_min || '', node.proof_max || ''].filter(Boolean).join(' -> '); const sources = Object.entries(node.proof_status_by_source || {}).map(([key,value]) => `${key}=${value}`).join(', '); return `<tr><td>${escapeHtml(node.label || node.id || '')}</td><td>${escapeHtml(node.type || '')}</td><td>${escapeHtml(node.proof_badge || node.proof_status || '')}</td><td>${escapeHtml(range)}</td><td>${escapeHtml(sources)}</td></tr>`; }",
            "function edgeRow(edge){ return `<tr><td>${escapeHtml(edge.from || '')}</td><td>${escapeHtml(edge.relation || '')}</td><td>${escapeHtml(edge.proof_status || '')}</td><td>${escapeHtml(edge.to || '')}</td><td>${escapeHtml(edge.source || '')}</td></tr>`; }",
            "function escapeHtml(value){ return String(value).replace(/[&<>\"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',\"'\":'&#39;'}[char])); }",
            "})();",
            "</script>",
            "</section>",
        ]
    )


def write_visualization(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report["content"], encoding="utf-8", newline="\n")


def compare_timeline_detail(match: dict[str, Any]) -> list[str]:
    detail = []
    for key in ("status", "mirror_status", "actual_proof_status"):
        value = match.get(key)
        if value not in (None, "", []):
            detail.append(f"{key}={value}")
    detail.extend(compare_boundary_evidence(match)[:4])
    detail.extend(f"runtime_gap={gap}" for gap in string_items(match.get("runtime_evidence_gaps"))[:2])
    detail.extend(string_items(match.get("gaps"))[:2])
    return unique_list(detail)


def compare_boundary_evidence(match: dict[str, Any]) -> list[str]:
    return [
        str(item)
        for item in string_items(match.get("evidence"))
        if any(str(item).startswith(prefix) for prefix in COMPARE_BOUNDARY_EVIDENCE_PREFIXES)
    ]


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
    addresses: list[str] | None = None,
    severity: int = 0,
    proof_status: Any = None,
    evidence_atoms: Any = None,
) -> dict[str, Any]:
    proof = normalize_proof_status(proof_status)
    bank_state_detail = " ".join(bank_state_record_evidence_from_atoms(evidence_atoms))
    event = {
        "lane": lane,
        "type": event_type,
        "event_type": event_type,
        "title": title,
        "source": source,
        "frame": frame,
        "order": int(order),
        "detail": " ".join(part for part in (detail, bank_state_detail) if part),
        "symbols": unique_list([item for item in symbols or [] if item]),
        "files": unique_list([item for item in files or [] if item]),
        "addresses": unique_list([item for item in addresses or [] if item]),
        "severity": int(severity),
    }
    if proof:
        event["proof_status"] = proof
        if "proof=" not in event["detail"]:
            event["detail"] = " ".join([part for part in (event["detail"], f"proof={proof}") if part])
    return event


def waterfall_step(*, phase: str, title: str, source: str, status: str, detail: str, order: int) -> dict[str, Any]:
    return {
        "phase": phase,
        "title": title,
        "source": source,
        "status": status,
        "detail": detail,
        "order": int(order),
    }


def collect_emulator_frames(
    *,
    loaded_reports: list[dict[str, Any]],
    loaded_traces: list[dict[str, Any]],
    max_frames: int,
) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    for loaded in loaded_reports:
        collect_emulator_frame_records(
            loaded["data"],
            source=loaded["source"],
            out=frames,
            parent="",
        )
    for loaded in loaded_traces:
        collect_emulator_frame_records(
            loaded["data"],
            source=loaded["source"],
            out=frames,
            parent="",
        )
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for frame in sorted(frames, key=emulator_frame_sort_key):
        key = (
            str(frame.get("source", "")),
            str(frame.get("frame", "")),
            str(frame.get("pc_bank_address", "")),
            str(frame.get("pc_label", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(frame)
        if len(unique) >= max(0, max_frames):
            break
    return unique


def collect_emulator_frame_records(data: Any, *, source: str, out: list[dict[str, Any]], parent: str) -> None:
    if isinstance(data, dict):
        next_parent = str(data.get("title") or data.get("kind") or data.get("event_type") or parent)
        if looks_like_emulator_frame(data):
            out.append(normalize_emulator_frame(data, source=source, parent=parent))
        dynamic_context = data.get("dynamic_context") if isinstance(data.get("dynamic_context"), dict) else {}
        for relation in ("prelude", "after"):
            nested = dynamic_context.get(relation)
            if isinstance(nested, list):
                for item in nested:
                    collect_emulator_frame_records(
                        attach_frame_relation(item, relation=relation, parent=next_parent),
                        source=source,
                        out=out,
                        parent=next_parent,
                    )
            elif isinstance(nested, dict):
                collect_emulator_frame_records(
                    attach_frame_relation(nested, relation=relation, parent=next_parent),
                    source=source,
                    out=out,
                    parent=next_parent,
                )
        for key, value in data.items():
            if key == "dynamic_context":
                continue
            collect_emulator_frame_records(value, source=source, out=out, parent=next_parent)
    elif isinstance(data, list):
        for item in data:
            collect_emulator_frame_records(item, source=source, out=out, parent=parent)


def attach_frame_relation(data: Any, *, relation: str, parent: str) -> Any:
    if not isinstance(data, dict):
        return data
    attached = dict(data)
    attached.setdefault("relation", relation)
    attached.setdefault("parent", parent)
    return attached


def looks_like_emulator_frame(data: dict[str, Any]) -> bool:
    if not isinstance(data, dict):
        return False
    has_order = any(key in data for key in ("frame", "seq", "cycle", "instruction_index"))
    has_emulator_state = any(
        key in data
        for key in (
            "pc",
            "pc_label",
            "pc_bank_address",
            "registers",
            "watch_values",
            "mnemonic",
            "screenshot",
            "screen_image",
            "frame_image",
            "framebuffer",
            "tilemap",
        )
    )
    return has_order and has_emulator_state


def normalize_emulator_frame(data: dict[str, Any], *, source: str, parent: str) -> dict[str, Any]:
    frame = first_present(data, ("frame", "seq", "cycle", "instruction_index"))
    registers = dict_items_from_mapping(data.get("registers"))
    for key, value in data.items():
        if str(key).startswith("register_"):
            registers[str(key).removeprefix("register_")] = str(value)
    watch_values = dict_items_from_mapping(data.get("watch_values"))
    for key in ("watch", "target", "sink"):
        name = str(data.get(key) or "")
        if name and data.get("new_hex") is not None:
            watch_values.setdefault(name, str(data.get("new_hex")))
    image = first_string(data, ("screenshot", "screen_image", "frame_image", "image"))
    framebuffer = first_string(data, ("framebuffer", "tilemap"))
    return {
        "source": source,
        "frame": frame,
        "kind": str(data.get("kind") or data.get("type") or "emulator_frame"),
        "event_type": str(data.get("event_type") or data.get("relation") or ""),
        "parent": str(data.get("parent") or parent),
        "pc": str(data.get("pc") or ""),
        "pc_bank": str(data.get("pc_bank") or ""),
        "pc_bank_address": str(data.get("pc_bank_address") or ""),
        "pc_label": str(data.get("pc_label") or data.get("function") or ""),
        "mnemonic": str(data.get("mnemonic") or ""),
        "registers": registers,
        "watch_values": watch_values,
        "image": image,
        "framebuffer": framebuffer,
        "detail": emulator_frame_detail(data),
    }


def emulator_frame_detail(data: dict[str, Any]) -> str:
    parts = [
        str(data.get("mnemonic") or ""),
        str(data.get("bank_address") or ""),
        str(data.get("address") or ""),
    ]
    return " ".join(part for part in parts if part)


def emulator_frame_sort_key(item: dict[str, Any]) -> tuple[Any, ...]:
    frame = item.get("frame")
    try:
        frame_sort = int(frame)
    except (TypeError, ValueError):
        frame_sort = 10**9
    return (
        str(item.get("source", "")),
        frame_sort,
        str(item.get("pc_bank_address", "")),
        str(item.get("pc_label", "")),
    )


def inspector_item_count(
    *,
    timeline: list[dict[str, Any]],
    waterfall: list[dict[str, Any]],
    graph: dict[str, list[dict[str, Any]]],
    emulator_frames: list[dict[str, Any]],
) -> int:
    return len(timeline) + len(waterfall) + len(graph["nodes"]) + len(graph["edges"]) + len(emulator_frames)


def trace_observations(data: Any) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    walk_trace(data, out=out)
    return out


def walk_trace(data: Any, *, out: list[dict[str, str]]) -> None:
    if isinstance(data, dict):
        symbol = first_string(data, ("full_symbol", "symbol", "pc_label", "watch", "resolved", "query"))
        source_file = first_string(data, ("source_file",))
        rule_id = first_string(data, ("rule_id",))
        address = first_string(data, ("bank_address", "address"))
        if symbol or source_file or rule_id or address:
            out.append({"symbol": symbol, "source_file": source_file, "rule_id": rule_id, "address": address})
        for value in data.values():
            walk_trace(value, out=out)
    elif isinstance(data, list):
        for item in data:
            walk_trace(item, out=out)


def collect_reverse_query_address_boundary_graph(
    result: dict[str, Any],
    *,
    source: str,
    label: str,
    query_id: str,
    query_proof: str,
    nodes: dict[str, dict[str, Any]],
    edges: dict[tuple[str, str, str], dict[str, Any]],
) -> None:
    requested = result.get("requested_static_address") if isinstance(result.get("requested_static_address"), dict) else {}
    observed = result.get("observed_runtime_address") if isinstance(result.get("observed_runtime_address"), dict) else {}
    boundary = result.get("address_fact_boundary") if isinstance(result.get("address_fact_boundary"), dict) else {}
    if not requested and not observed and not boundary:
        return
    boundary_fields = reverse_query_address_boundary_fields(result)
    boundary_evidence = reverse_query_address_boundary_evidence(result)
    requested_key = str(requested.get("address_key") or requested.get("address") or "")
    observed_key = str(observed.get("address_key") or observed.get("address") or "")
    requested_id = ""
    observed_id = ""
    if requested_key:
        requested_id = f"{source}:requested_static_address:{label}:{requested_key}"
        requested_node = add_graph_node(
            nodes,
            requested_id,
            f"Requested static address {requested_key}",
            "requested_static_address",
            source,
            "planned_only",
        )
        if requested_node is not None:
            requested_node.update(boundary_fields)
            requested_node["addresses"] = unique_list([*string_items(requested_node.get("addresses")), requested_key])
            requested_node["evidence"] = unique_list([*string_items(requested_node.get("evidence")), *boundary_evidence])
        edge = add_graph_edge(edges, query_id, requested_id, "requests_static_address", source, "planned_only")
        if edge is not None:
            edge.update(boundary_fields)
            edge["evidence"] = unique_list([*string_items(edge.get("evidence")), *boundary_evidence])
    if observed_key:
        observed_id = f"{source}:observed_runtime_address:{label}:{observed_key}:{result.get('last_writer_seq', '')}"
        observed_proof = normalize_proof_status(observed.get("proof_status")) or query_proof
        observed_node = add_graph_node(
            nodes,
            observed_id,
            f"Observed runtime address {observed_key}",
            "observed_runtime_address",
            source,
            observed_proof,
        )
        if observed_node is not None:
            observed_node.update(boundary_fields)
            observed_node["addresses"] = unique_list([*string_items(observed_node.get("addresses")), observed_key])
            observed_node["evidence"] = unique_list([*string_items(observed_node.get("evidence")), *boundary_evidence])
        edge = add_graph_edge(edges, observed_id, query_id, "supplies_runtime_address", source, observed_proof)
        if edge is not None:
            edge.update(boundary_fields)
            edge["evidence"] = unique_list([*string_items(edge.get("evidence")), *boundary_evidence])
    if requested_id and observed_id:
        boundary_proof = query_proof if boundary.get("exact_runtime_address_proven") is True else "planned_only"
        edge = add_graph_edge(edges, requested_id, observed_id, "address_fact_boundary", source, boundary_proof)
        if edge is not None:
            edge.update(boundary_fields)
            edge["evidence"] = unique_list([*string_items(edge.get("evidence")), *boundary_evidence])


def collect_hardware_regression_graph(
    data: dict[str, Any],
    *,
    source: str,
    nodes: dict[str, dict[str, Any]],
    edges: dict[tuple[str, str, str], dict[str, Any]],
) -> None:
    gate_id = f"{source}:hardware_regression_gate"
    gate_proof = normalize_proof_status(data.get("proof_status")) or "planned_only"
    add_graph_node(nodes, gate_id, "Pan Docs hardware regression gate", "hardware_regression_gate", source, gate_proof)
    for case in dict_items(data.get("cases")):
        case_id = f"{source}:hardware_case:{case.get('id', '')}"
        case_proof = normalize_proof_status(case.get("proof_status")) or "planned_only"
        case_node = add_graph_node(
            nodes,
            case_id,
            str(case.get("title") or case.get("id") or "hardware case"),
            "hardware_regression_case",
            source,
            case_proof,
        )
        if case_node is not None:
            case_node["evidence"] = unique_list(
                [*string_items(case_node.get("evidence")), *hardware_regression_case_evidence(case)]
            )
            case_node["hardware_behavior_proven"] = bool(case.get("hardware_behavior_proven"))
            case_node["hardware_proof_fact_count"] = int_value(case.get("hardware_proof_fact_count"))
            case_node["observed_runtime_fact_count"] = int_value(case.get("observed_runtime_fact_count"))
        add_graph_edge(edges, gate_id, case_id, "contains_hardware_case", source, case_proof)
        for index, fact in enumerate(dict_items(case.get("observed_runtime_facts"))):
            fact_id = f"{case_id}:observed_runtime_fact:{index}:{fact.get('fact_type', '')}"
            fact_node = add_graph_node(
                nodes,
                fact_id,
                str(fact.get("fact_type") or "observed runtime fact"),
                "hardware_runtime_fact",
                source,
                "planned_only",
            )
            if fact_node is not None:
                fact_node["evidence"] = unique_list(
                    [*string_items(fact_node.get("evidence")), *hardware_fact_evidence("observed_runtime_fact", fact)]
                )
                fact_node["proof_scope"] = str(fact.get("proof_scope") or "")
            add_graph_edge(edges, fact_id, case_id, "observes_runtime_not_case_proof", source, "planned_only")
        for index, fact in enumerate(dict_items(case.get("hardware_proof_facts"))):
            fact_id = f"{case_id}:hardware_proof_fact:{index}:{fact.get('fact_type', '')}"
            fact_node = add_graph_node(
                nodes,
                fact_id,
                str(fact.get("fact_type") or "hardware proof fact"),
                "hardware_proof_fact",
                source,
                case_proof,
            )
            if fact_node is not None:
                fact_node["evidence"] = unique_list(
                    [*string_items(fact_node.get("evidence")), *hardware_fact_evidence("hardware_proof_fact", fact)]
                )
                fact_node["proof_scope"] = str(fact.get("proof_scope") or "")
            add_graph_edge(edges, fact_id, case_id, "proves_hardware_case", source, case_proof)
        for index, fact in enumerate(dict_items(case.get("static_blocker_facts"))):
            fact_id = f"{case_id}:static_blocker_fact:{index}:{fact.get('fact_type', '')}"
            fact_node = add_graph_node(
                nodes,
                fact_id,
                str(fact.get("fact_type") or "static blocker fact"),
                "hardware_static_blocker_fact",
                source,
                "planned_only",
            )
            if fact_node is not None:
                fact_node["evidence"] = unique_list(
                    [*string_items(fact_node.get("evidence")), *hardware_fact_evidence("static_blocker_fact", fact)]
                )
                fact_node["proof_scope"] = str(fact.get("proof_scope") or "")
            add_graph_edge(edges, fact_id, case_id, "blocks_hardware_case", source, "planned_only")


def hardware_regression_case_detail(case: dict[str, Any]) -> str:
    return " ".join(hardware_regression_case_evidence(case)[:12])


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
    return unique_list([item for item in evidence if item and not item.endswith("=")])


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


def add_graph_node(
    nodes: dict[str, dict[str, Any]],
    node_id: str,
    label: str,
    node_type: str,
    source: str,
    proof_status: Any = None,
    *,
    proof_status_by_source: Any = None,
    proof_summary: Any = None,
    evidence_atoms: Any = None,
) -> dict[str, Any] | None:
    if not node_id:
        return None
    safe = safe_id(node_id)
    node = nodes.setdefault(
        safe,
        {
            "id": safe,
            "label": label or node_id,
            "type": node_type or "node",
            "source": source,
            "sources": [],
            "proof_status_by_source": {},
            "proof_status_counts": {},
        },
    )
    proof = normalize_proof_status(proof_status)
    node["sources"] = unique_list([*string_items(node.get("sources")), source])
    if proof:
        node["proof_status"] = strongest_proof_status([node.get("proof_status"), proof])
        proof_counts = node.get("proof_status_counts")
        if not isinstance(proof_counts, dict):
            proof_counts = {}
        proof_counts[proof] = int(proof_counts.get(proof, 0) or 0) + 1
        node["proof_status_counts"] = dict(sorted(proof_counts.items()))
    source_proofs = node.get("proof_status_by_source")
    if not isinstance(source_proofs, dict):
        source_proofs = {}
    if isinstance(proof_status_by_source, dict):
        for key, value in proof_status_by_source.items():
            source_key = str(key or "")
            if not source_key:
                continue
            source_proofs[source_key] = strongest_proof_status([source_proofs.get(source_key), value])
    elif source:
        source_proofs[str(source)] = strongest_proof_status([source_proofs.get(str(source)), proof])
    for key, value in bank_state_record_proof_status_by_source(evidence_atoms).items():
        source_proofs[key] = strongest_proof_status([source_proofs.get(key), value])
    node["proof_status_by_source"] = dict(sorted(source_proofs.items()))
    summary = (
        normalized_graph_node_proof_summary(proof_summary)
        or graph_node_proof_summary_from_counts_and_sources(
            node.get("proof_status_counts"),
            source_proofs,
        )
        or graph_node_proof_summary(source_proofs.values())
    )
    node["proof_summary"] = summary
    node["proof_min"] = summary["min"]
    node["proof_max"] = summary["max"]
    node["proof_badge"] = graph_node_proof_badge(summary)
    return node


def add_graph_edge(
    edges: dict[tuple[str, str, str], dict[str, Any]],
    source_id: str,
    target_id: str,
    relation: str,
    source: str,
    proof_status: Any = None,
) -> dict[str, Any] | None:
    if not source_id or not target_id:
        return None
    from_id = safe_id(source_id)
    to_id = safe_id(target_id)
    key = (from_id, to_id, relation)
    edge = edges.setdefault(
        key,
        {
            "from": from_id,
            "to": to_id,
            "relation": relation or "relates",
            "source": source,
        },
    )
    proof = normalize_proof_status(proof_status)
    if proof:
        edge["proof_status"] = strongest_proof_status([edge.get("proof_status"), proof])
    return edge


def dynamic_taint_path_proof_status(path: dict[str, Any]) -> str:
    explicit = normalize_proof_status(path.get("proof_status")) if path.get("proof_status") else ""
    if explicit:
        return explicit
    atom_statuses = [
        normalize_proof_status(atom.get("proof_status"))
        for atom in evidence_atoms(path.get("evidence_atoms"))
        if atom.get("proof_status")
    ]
    if atom_statuses:
        return weakest_proof_status(atom_statuses)
    return "planned_only"


def visual_snapshot_has_runtime_samples(data: dict[str, Any]) -> bool:
    screen_frame = data.get("screen_frame") if isinstance(data.get("screen_frame"), dict) else {}
    io_registers = data.get("io_registers") if isinstance(data.get("io_registers"), dict) else {}
    return bool(
        dict_items(data.get("surfaces"))
        or io_registers
        or screen_frame
        or data.get("framebuffer")
        or int_value(data.get("screen_frame_count"))
    )


def audio_snapshot_has_runtime_samples(data: dict[str, Any]) -> bool:
    registers = data.get("registers") if isinstance(data.get("registers"), dict) else {}
    wave = data.get("wave_ram") if isinstance(data.get("wave_ram"), dict) else {}
    sound_buffer = data.get("sound_buffer") if isinstance(data.get("sound_buffer"), dict) else {}
    return bool(
        registers
        or dict_items(data.get("register_details"))
        or dict_items(data.get("symbol_state"))
        or wave.get("sha256")
        or wave.get("sample_hex")
        or sound_buffer.get("sha256")
        or sound_buffer.get("sample_hex")
        or sound_buffer.get("buffer")
    )


def snapshot_report_proof_status(
    data: dict[str, Any],
    *,
    runtime_samples: bool,
    downgrade_reason: str,
) -> str:
    explicit = normalize_proof_status(data.get("proof_status")) if data.get("proof_status") else ""
    if runtime_samples:
        return explicit or ("runtime_observed" if data.get("executed") else "planned_only")
    if snapshot_proof_downgrade_detail(
        data,
        runtime_samples=runtime_samples,
        downgrade_reason=downgrade_reason,
    ):
        return "planned_only"
    return explicit or "planned_only"


def snapshot_proof_downgrade_detail(
    data: dict[str, Any],
    *,
    runtime_samples: bool,
    downgrade_reason: str,
) -> str:
    explicit = normalize_proof_status(data.get("proof_status")) if data.get("proof_status") else ""
    if runtime_samples:
        return ""
    if bool(data.get("executed")) or explicit in {
        "runtime_observed",
        "instruction_observed",
        "taint_proven",
        "mirror_passed",
        "mirror_failed",
    }:
        return f" proof_downgrade_reason={downgrade_reason}"
    return ""


def watch_event_proof_status(event: dict[str, Any], *, report: dict[str, Any]) -> str:
    explicit = normalize_proof_status(event.get("proof_status")) if event.get("proof_status") else ""
    if explicit:
        return explicit
    report_proof = normalize_proof_status(report.get("proof_status")) if report.get("proof_status") else ""
    if report_proof:
        return report_proof
    return "planned_only"


def effect_item_proof_status(effect: dict[str, Any]) -> str:
    if effect.get("hardware_event_required") and not effect.get("hardware_runtime_event"):
        return "planned_only"
    if str(effect.get("hardware_proof_gate") or "") == "explicit_runtime_event_missing":
        return "planned_only"
    explicit = normalize_proof_status(effect.get("proof_status")) if effect.get("proof_status") else ""
    if explicit:
        return explicit
    atom_statuses = [
        normalize_proof_status(atom.get("proof_status"))
        for atom in evidence_atoms(effect.get("evidence_atoms"))
    ]
    if atom_statuses:
        return weakest_proof_status(atom_statuses)
    return "planned_only"


def effect_trace_report_graph_proof_status(data: dict[str, Any]) -> str:
    statuses = effect_trace_report_effect_proof_statuses(data)
    if statuses:
        return weakest_proof_status(statuses)
    report_proof = normalize_proof_status(data.get("proof_status")) if data.get("proof_status") else ""
    return report_proof or "planned_only"


def effect_trace_report_graph_proof_summary(data: dict[str, Any], *, report_proof: str) -> dict[str, Any]:
    statuses = [report_proof]
    top_level = normalize_proof_status(data.get("proof_status")) if data.get("proof_status") else ""
    if top_level:
        statuses.append(top_level)
    statuses.extend(effect_trace_report_effect_proof_statuses(data))
    return graph_node_proof_summary(statuses)


def effect_trace_report_effect_proof_statuses(data: dict[str, Any]) -> list[str]:
    counts = data.get("effect_proof_status_counts") if isinstance(data.get("effect_proof_status_counts"), dict) else {}
    statuses = [
        status
        for status, count in counts.items()
        if normalize_proof_status(status) and int_value(count) > 0
    ]
    if statuses:
        return unique_list([normalize_proof_status(status) for status in statuses])
    return unique_list(
        [
            effect_item_proof_status(effect)
            for event in dict_items(data.get("events"))
            for effect in dict_items(event.get("effects"))
        ]
    )


def attach_effect_trace_report_graph_fields(node: dict[str, Any], data: dict[str, Any]) -> None:
    counts = data.get("effect_proof_status_counts") if isinstance(data.get("effect_proof_status_counts"), dict) else {}
    if counts:
        node["effect_proof_status_counts"] = {
            str(status): int_value(count)
            for status, count in sorted(counts.items())
            if normalize_proof_status(status) and int_value(count) > 0
        }
    for key in (
        "hardware_gated_effect_count",
        "hardware_runtime_event_effect_count",
        "hardware_side_effect_count",
        "dma_copy_write_count",
        "interrupt_entry_count",
    ):
        if data.get(key) not in {None, ""}:
            node[key] = int_value(data.get(key))


def watch_hit_proof_status(hit: dict[str, Any]) -> str:
    statuses: list[str] = []
    effect_proof = normalize_proof_status(hit.get("effect_proof_status")) if hit.get("effect_proof_status") else ""
    if effect_proof:
        statuses.append(effect_proof)
    if hit.get("hardware_event_required") and not hit.get("hardware_runtime_event"):
        statuses.append("planned_only")
    if str(hit.get("hardware_proof_gate") or "") == "explicit_runtime_event_missing":
        statuses.append("planned_only")
    explicit = normalize_proof_status(hit.get("proof_status")) if hit.get("proof_status") else ""
    if explicit:
        statuses.append(explicit)
    target_match = normalize_proof_status(hit.get("target_match_proof_status")) if hit.get("target_match_proof_status") else ""
    if target_match:
        statuses.append(target_match)
    if str(hit.get("bank_match") or "") in {"bus_address_unverified_bank", "ambiguous_runtime_bank"}:
        statuses.append("planned_only")
    return weakest_proof_status(statuses) or "planned_only"


def instruction_trace_validation_proof_status(data: dict[str, Any], validation: dict[str, Any]) -> str:
    validation_proof = normalize_proof_status(validation.get("proof_status")) if validation.get("proof_status") else ""
    if validation_proof:
        return validation_proof
    report_proof = normalize_proof_status(data.get("proof_status")) if data.get("proof_status") else ""
    if report_proof:
        return report_proof
    return "planned_only"


def reverse_query_result_proof_status(result: dict[str, Any], *, report: dict[str, Any] | None = None) -> str:
    if reverse_query_address_boundary_blocks_proof(result):
        return "planned_only"
    explicit = normalize_proof_status(result.get("proof_status")) if result.get("proof_status") else ""
    if explicit:
        return explicit
    validation = result.get("validation") if isinstance(result.get("validation"), dict) else {}
    validation_proof = normalize_proof_status(validation.get("proof_status")) if validation.get("proof_status") else ""
    if validation_proof:
        return validation_proof
    report_proof = normalize_proof_status(report.get("proof_status")) if isinstance(report, dict) and report.get("proof_status") else ""
    if report_proof:
        return report_proof
    return "instruction_observed" if concrete_reverse_last_writer(result) else "planned_only"


def concrete_reverse_last_writer(result: dict[str, Any]) -> bool:
    last_writer = result.get("last_writer") if isinstance(result.get("last_writer"), dict) else {}
    if not last_writer:
        return False
    seq = last_writer.get("seq", result.get("last_writer_seq"))
    if seq is None or str(seq) == "":
        return False
    pc = str(last_writer.get("pc_label") or last_writer.get("pc") or result.get("last_writer_pc") or "")
    address = str(last_writer.get("address") or last_writer.get("address_key") or result.get("matched_address") or "")
    if not pc or not address:
        return False
    access = str(last_writer.get("access") or "").lower()
    kind = str(last_writer.get("kind") or "").lower()
    if access and "write" not in access:
        return False
    if kind and kind not in {"write", "memory_write", "stack_write", "watch_hit"}:
        return False
    return True


def strongest_proof_status(values: list[Any]) -> str:
    return shared_strongest_proof_status(values, default="")


def weakest_proof_status(values: Any) -> str:
    return shared_weakest_proof_status(values, default="")


def side_effect_index_proof_status(item: dict[str, Any]) -> str:
    explicit = normalize_proof_status(item.get("proof_status")) if item.get("proof_status") else ""
    if explicit:
        return explicit
    trigger_statuses = [
        normalize_proof_status(trigger.get("proof_status"))
        for trigger in dict_items(item.get("triggers"))
        if trigger.get("proof_status")
    ]
    if trigger_statuses:
        return weakest_proof_status(trigger_statuses)
    return "instruction_observed"


def graph_node_proof_summary(values: Any) -> dict[str, Any]:
    statuses = [normalize_proof_status(value) for value in values]
    statuses = [status for status in statuses if status]
    return {
        "max": strongest_proof_status(statuses),
        "min": weakest_proof_status(statuses),
        "source_count": len(statuses),
    }


def graph_node_proof_summary_from_counts_and_sources(
    counts: Any,
    source_proofs: dict[str, Any],
) -> dict[str, Any] | None:
    if not isinstance(counts, dict):
        counts = {}
    statuses = [
        normalize_proof_status(status)
        for status, count in counts.items()
        if normalize_proof_status(status) and int_value(count) > 0
    ]
    statuses.extend(
        normalize_proof_status(status)
        for status in source_proofs.values()
        if normalize_proof_status(status)
    )
    if not statuses:
        return None
    summary = graph_node_proof_summary(statuses)
    summary["source_count"] = len(source_proofs)
    summary["status_count"] = sum(int_value(count) for count in counts.values())
    return summary


def normalized_graph_node_proof_summary(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    min_status = normalize_proof_status(value.get("min"))
    max_status = normalize_proof_status(value.get("max"))
    if not min_status and not max_status:
        return None
    source_count = int_value(value.get("source_count"))
    if source_count <= 0:
        source_count = int(bool(min_status)) + int(bool(max_status and max_status != min_status))
    return {
        "max": max_status or min_status,
        "min": min_status or max_status,
        "source_count": source_count,
        **({"status_count": int_value(value.get("status_count"))} if int_value(value.get("status_count")) > 0 else {}),
    }


def graph_node_proof_badge(summary: dict[str, Any]) -> str:
    min_status = str(summary.get("min") or "")
    max_status = str(summary.get("max") or "")
    if min_status and max_status and min_status != max_status:
        return "mixed"
    return max_status or min_status


def graph_node_mermaid_label(node: dict[str, Any]) -> str:
    label = str(node.get("label") or node.get("id") or "")
    if node.get("proof_badge") != "mixed":
        return label
    return f"{label}\nproof:mixed {node.get('proof_min', '')}->{node.get('proof_max', '')}"


def mixed_proof_nodes(graph: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [
        node
        for node in graph.get("nodes", [])
        if node.get("proof_badge") == "mixed"
    ]


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
    }
    return (phase_order.get(item.get("phase", ""), 50), item.get("source", ""), item.get("order", 0), item.get("title", ""))


def command_status(command: str) -> str:
    if not command:
        return "planned"
    if "<" in command or ">" in command:
        return "needs-input"
    return "runnable"


def state_patch_minimization_detail(item: dict[str, Any]) -> str:
    parts = [
        f"patches={item.get('original_patch_count', 0)}->{item.get('minimized_patch_count', 0)}",
        f"semantic_watch={item.get('semantic_watch_rerun_count', 0)}/{item.get('semantic_watch_rerun_attempt_count', 0)}",
        f"semantic_replay={item.get('semantic_replay_rerun_count', 0)}/{item.get('semantic_replay_rerun_attempt_count', 0)}",
        *save_state_delta_evidence(
            minimized_state_patch_save_state_delta(item),
            prefix="minimized_save_state_delta",
        ),
    ]
    watch_addresses = string_items(item.get("watch_addresses"))
    source_mems = string_items(item.get("source_mems"))
    if watch_addresses:
        parts.append("watch_addresses=" + ",".join(watch_addresses[:6]))
    if source_mems:
        parts.append("source_mems=" + ",".join(source_mems[:6]))
    if item.get("out_report"):
        parts.append("out_report=" + str(item.get("out_report")))
    return " ".join(parts)


def semantic_reducer_route_detail(route: dict[str, Any]) -> str:
    parts = [
        f"surface={route.get('surface', '')}",
        f"commands={route.get('command_count', len(string_items(route.get('commands'))))}",
        str(route.get("reason", "")),
    ]
    source_file = str(route.get("source_file", ""))
    if source_file:
        parts.append(f"source_file={source_file}")
    return " ".join(part for part in parts if part)


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
    return unique_list(addresses)


def trace_synthesis_routes(data: dict[str, Any]) -> list[dict[str, Any]]:
    plan = data.get("trace_synthesis_plan") if isinstance(data.get("trace_synthesis_plan"), dict) else {}
    return dict_items(plan.get("routes"))


def trace_synthesis_title(route: dict[str, Any]) -> str:
    match_id = str(route.get("match_id") or route.get("source_kind") or route.get("id") or "route")
    return f"Dynamic-taint trace synthesis: {match_id}"


def trace_synthesis_detail(route: dict[str, Any]) -> str:
    parts = [
        f"state={route.get('state_status', '')}",
        f"scenario={','.join(string_items(route.get('scenario_ids'))[:4])}",
        f"sources={','.join(trace_synthesis_related_symbols(route)[:4])}",
        f"source_mems={','.join(string_items(route.get('source_mems'))[:4])}",
        f"trace={route.get('trace_output', '')}",
    ]
    return " ".join(part for part in parts if not part.endswith("="))


def trace_synthesis_severity(route: dict[str, Any]) -> int:
    status = str(route.get("state_status", ""))
    return 66 if status.startswith("requires") else 62


def trace_synthesis_related_symbols(route: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            *string_items(route.get("sink_symbols")),
            *string_items(route.get("source_symbols")),
            *source_mem_origins(route),
        ]
    )


def trace_synthesis_related_addresses(route: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            *string_items(route.get("sink_addresses")),
            *source_mem_addresses(route),
        ]
    )


def side_effect_timeline_title(item: dict[str, Any]) -> str:
    operations = side_effect_trigger_values(item, "operation")
    operation_text = "/".join(operation.upper() for operation in operations[:3])
    if operation_text:
        return f"{item.get('kind', 'side_effect')} {operation_text}"
    return f"{item.get('kind', 'side_effect')} side effect"


def effect_watch_hit_detail(hit: dict[str, Any], event: dict[str, Any]) -> str:
    return " ".join(
        part
        for part in [
            f"pc={event.get('pc_bank_address', '')}",
            f"pc_label={event.get('pc_label', '')}",
            f"operation={hit.get('operation', '')}" if hit.get("operation") else "",
            f"value={hit.get('value_hex', '')}" if hit.get("value_hex") else "",
            f"bank_match={hit.get('bank_match', '')}" if hit.get("bank_match") else "",
            f"bank_source={hit.get('bank_source', '')}" if hit.get("bank_source") else "",
            f"evidence_source={hit.get('effect_evidence_source', '')}" if hit.get("effect_evidence_source") else "",
            f"effect_proof_status={hit.get('effect_proof_status', '')}" if hit.get("effect_proof_status") else "",
            f"target_match_proof_status={hit.get('target_match_proof_status', '')}"
            if hit.get("target_match_proof_status")
            else "",
            f"hardware_proof_gate={hit.get('hardware_proof_gate', '')}" if hit.get("hardware_proof_gate") else "",
            f"proof_downgrade_reason={hit.get('proof_downgrade_reason', '')}" if hit.get("proof_downgrade_reason") else "",
        ]
        if part
    )


def effect_post_value_title(effect: dict[str, Any]) -> str:
    address = str(effect.get("address_hex") or effect.get("address") or "<address>")
    status = str(effect.get("post_value_status") or "observed")
    return f"Post-write value {status} at {address}"


def effect_post_value_detail(effect: dict[str, Any], event: dict[str, Any]) -> str:
    return " ".join(
        part
        for part in [
            f"pc={event.get('pc_bank_address', '')}",
            f"pc_label={event.get('pc_label', '')}",
            f"operation={effect.get('operation', '')}" if effect.get("operation") else "",
            f"modeled={effect.get('value_hex', '')}" if effect.get("value_hex") else "",
            f"observed={effect.get('post_value_hex', '')}" if effect.get("post_value_hex") else "",
            f"next_pc={effect.get('post_observed_pc', '')}" if effect.get("post_observed_pc") else "",
            f"status={effect.get('post_value_status', '')}" if effect.get("post_value_status") else "",
            f"proof_status={effect_item_proof_status(effect)}",
            f"hardware_proof_gate={effect.get('hardware_proof_gate', '')}" if effect.get("hardware_proof_gate") else "",
        ]
        if part
    )


def effect_post_value_addresses(effect: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            str(effect.get("address_hex") or effect.get("address") or ""),
            str(effect.get("address_key") or ""),
        ]
    )


def effect_register_write_title(effect: dict[str, Any]) -> str:
    register = str(effect.get("register") or "<register>")
    return f"{register} register write"


def effect_register_validation_title(effect: dict[str, Any]) -> str:
    register = str(effect.get("register") or "<register>")
    status = str(effect.get("post_register_status") or "observed")
    return f"Post-register value {status} for {register}"


def effect_register_write_detail(effect: dict[str, Any], event: dict[str, Any]) -> str:
    return " ".join(
        part
        for part in [
            f"pc={event.get('pc_bank_address', '')}",
            f"pc_label={event.get('pc_label', '')}",
            f"operation={effect.get('operation', '')}" if effect.get("operation") else "",
            f"register={effect.get('register', '')}" if effect.get("register") else "",
            f"value={effect.get('value_hex', '')}" if effect.get("value_hex") else "",
            f"post={effect.get('post_register_hex', '')}" if effect.get("post_register_hex") else "",
            f"status={effect.get('post_register_status', '')}" if effect.get("post_register_status") else "",
        ]
        if part
    )


def effect_source_addresses(effect: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            str(operand.get("address") or "")
            for operand in dict_items(effect.get("source_operands"))
            if operand.get("kind") == "memory"
        ]
    )


def effect_unmodeled_change_title(change: dict[str, Any]) -> str:
    address = str(change.get("address") or "<address>")
    return f"Unmodeled observed change at {address}"


def effect_unmodeled_change_detail(change: dict[str, Any], event: dict[str, Any]) -> str:
    return " ".join(
        part
        for part in [
            f"pc={change.get('pc') or event.get('pc_bank_address', '')}",
            f"pc_label={change.get('pc_label') or event.get('pc_label', '')}",
            f"old={change.get('old_value_hex', '')}" if change.get("old_value_hex") else "",
            f"new={change.get('new_value_hex', '')}" if change.get("new_value_hex") else "",
            f"next_pc={change.get('next_pc', '')}" if change.get("next_pc") else "",
            f"status={change.get('status', '')}" if change.get("status") else "",
        ]
        if part
    )


def effect_unmodeled_change_addresses(change: dict[str, Any]) -> list[str]:
    return unique_list([str(change.get("address") or "")])


def effect_unmodeled_effect_title(effect: dict[str, Any]) -> str:
    operation = str(effect.get("operation") or effect.get("kind") or "effect")
    return f"Unmodeled effect: {operation}"


def effect_unmodeled_effect_detail(effect: dict[str, Any], event: dict[str, Any]) -> str:
    return " ".join(
        part
        for part in [
            f"pc={event.get('pc_bank_address', '')}",
            f"pc_label={event.get('pc_label', '')}",
            f"operation={effect.get('operation', '')}" if effect.get("operation") else "",
            f"reason={effect.get('evidence_status', '')}" if effect.get("evidence_status") else "",
            "missing=" + ",".join(string_items(effect.get("missing_registers"))) if effect.get("missing_registers") else "",
            f"address_source={effect.get('address_source', '')}" if effect.get("address_source") else "",
        ]
        if part
    )


def side_effect_timeline_detail(item: dict[str, Any]) -> str:
    parts = [
        f"category={item.get('category', '')}",
        f"count={item.get('count', 0)}",
        f"last={item.get('last_pc', '')}",
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
    return " ".join(part for part in parts if part)


def side_effect_timeline_symbols(item: dict[str, Any]) -> list[str]:
    return unique_list(
        str(trigger.get("pc_label", ""))
        for trigger in dict_items(item.get("triggers"))
        if trigger.get("pc_label")
    )


def side_effect_trigger_values(item: dict[str, Any], key: str) -> list[str]:
    return unique_list(
        str(trigger.get(key, ""))
        for trigger in dict_items(item.get("triggers"))
        if trigger.get(key)
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


def is_boss_ai_report(data: dict[str, Any]) -> bool:
    source = str(data.get("source", ""))
    if source in {
        "trace_rom_pyboy_hooks",
        "python_scenario",
        "python_scenario_contributions",
    }:
        return True
    event_types = {str(event.get("event_type", "")) for event in dict_items(data.get("events"))}
    return bool(event_types & {"score_delta", "score_rule", "policy_check"}) and (
        data.get("scenario_id") is not None or data.get("trace_id") is not None
    )


def collect_boss_ai_timeline(data: dict[str, Any], *, source: str, out: list[dict[str, Any]]) -> None:
    proof = boss_ai_visual_proof(data)
    severity = 72 if proof == "runtime_observed" else 48
    if str(data.get("source", "")) == "python_scenario_contributions":
        out.append(
            timeline_event(
                lane="boss_ai",
                event_type="boss_ai_python_contribution_report",
                title="Boss AI Python contribution report",
                source=source,
                detail=(
                    f"traces={data.get('trace_count', 0)} events={data.get('event_count', 0)} "
                    f"changed={data.get('changed_event_count', 0)} proof={proof}"
                ),
                severity=severity,
            )
        )
        for trace in dict_items(data.get("traces"))[:20]:
            collect_boss_ai_trace_timeline(trace, source=source, out=out, proof=proof, severity=severity)
        return
    out.append(
        timeline_event(
            lane="boss_ai",
            event_type=boss_ai_trace_type(data),
            title=boss_ai_trace_title(data, fallback=source),
            source=source,
            detail=(
                f"events={data.get('event_count', 0)} changed={data.get('changed_event_count', 0)} "
                f"rules={data.get('rule_entry_count', data.get('covered_rule_count', 0))} proof={proof}"
            ),
            severity=severity,
        )
    )
    collect_boss_ai_trace_timeline(data, source=source, out=out, proof=proof, severity=severity)


def collect_boss_ai_trace_timeline(
    data: dict[str, Any],
    *,
    source: str,
    out: list[dict[str, Any]],
    proof: str,
    severity: int,
) -> None:
    for event in dict_items(data.get("events"))[:40]:
        event_type = str(event.get("event_type", ""))
        if event_type == "score_delta":
            out.append(
                timeline_event(
                    lane="boss_ai",
                    event_type="boss_ai_score_delta",
                    title=boss_ai_score_title(event),
                    source=source,
                    order=int_value(event.get("index")),
                    detail=boss_ai_score_detail(event, proof=proof),
                    symbols=boss_ai_event_symbols(event),
                    severity=severity,
                )
            )
        elif event_type == "score_rule":
            normalized = decision_score_event(event)
            out.append(
                timeline_event(
                    lane="boss_ai",
                    event_type="boss_ai_score_delta",
                    title=boss_ai_score_title(normalized),
                    source=source,
                    detail=boss_ai_score_detail(normalized, proof=proof),
                    symbols=boss_ai_event_symbols(normalized),
                    severity=severity,
                )
            )
        elif event_type == "policy_check":
            attrs = event.get("attributes") if isinstance(event.get("attributes"), dict) else event
            out.append(
                timeline_event(
                    lane="boss_ai",
                    event_type="boss_ai_policy_check",
                    title=f"Boss AI policy {attrs.get('verdict', '')}",
                    source=source,
                    detail=f"severity={attrs.get('severity', '')} reason={attrs.get('reason', '')} proof={proof}",
                    severity=severity,
                )
            )
    for event in dict_items(data.get("predicate_branch_entries"))[:30]:
        out.append(
            timeline_event(
                lane="boss_ai",
                event_type="boss_ai_predicate_branch",
                title=f"{event.get('predicate_id', 'predicate')} -> {event.get('outcome', '')}",
                source=source,
                order=int_value(event.get("index")),
                detail=f"rule={boss_ai_rule_id(source_info_from_event(event), event)} proof={proof}",
                symbols=boss_ai_event_symbols(event),
                severity=severity,
            )
        )
    for event in dict_items(data.get("public_read_probe_entries"))[:30]:
        out.append(
            timeline_event(
                lane="boss_ai",
                event_type="boss_ai_public_read_probe",
                title=f"{event.get('probe_id', 'probe')} -> {event.get('outcome', '')}",
                source=source,
                order=int_value(event.get("index")),
                detail=f"rule={boss_ai_rule_id(source_info_from_event(event), event)} proof={proof}",
                symbols=boss_ai_event_symbols(event),
                severity=severity,
            )
        )


def collect_boss_ai_graph(
    data: dict[str, Any],
    *,
    source: str,
    nodes: dict[str, dict[str, Any]],
    edges: dict[tuple[str, str, str], dict[str, Any]],
) -> None:
    if str(data.get("source", "")) == "python_scenario_contributions":
        root_id = f"{source}:boss_ai_python_contributions"
        add_graph_node(nodes, root_id, "Boss AI Python contributions", "boss_ai_python_contribution_report", source)
        for index, trace in enumerate(dict_items(data.get("traces"))[:40]):
            trace_id = f"{source}:boss_ai_trace:{index}:{trace.get('trace_id', trace.get('scenario_id', 'trace'))}"
            add_graph_node(nodes, trace_id, boss_ai_trace_title(trace, fallback=source), "boss_ai_python_contribution_trace", source)
            add_graph_edge(edges, root_id, trace_id, "contains_boss_ai_evidence", source)
            collect_boss_ai_trace_graph(trace, trace_id=trace_id, source=source, nodes=nodes, edges=edges)
        return
    trace_id = f"{source}:boss_ai_trace:{data.get('trace_id') or data.get('scenario_id') or data.get('save_state') or 'trace'}"
    add_graph_node(nodes, trace_id, boss_ai_trace_title(data, fallback=source), boss_ai_trace_type(data), source)
    chosen = data.get("chosen") if isinstance(data.get("chosen"), dict) else {}
    if chosen:
        choice_id = f"{source}:boss_ai_choice:{boss_ai_candidate_key(chosen)}"
        add_graph_node(nodes, choice_id, boss_ai_candidate_label(chosen), "boss_ai_choice", source)
        add_graph_edge(edges, trace_id, choice_id, "selects_action", source)
    collect_boss_ai_trace_graph(data, trace_id=trace_id, source=source, nodes=nodes, edges=edges)


def collect_boss_ai_trace_graph(
    data: dict[str, Any],
    *,
    trace_id: str,
    source: str,
    nodes: dict[str, dict[str, Any]],
    edges: dict[tuple[str, str, str], dict[str, Any]],
) -> None:
    for event in dict_items(data.get("rule_entries"))[:60]:
        source_info = source_info_from_event(event)
        rule_id = boss_ai_rule_id(source_info, event)
        if not rule_id:
            continue
        add_graph_node(nodes, rule_id, rule_id, "boss_ai_policy_rule", source)
        add_graph_edge(edges, trace_id, rule_id, "entered_policy_rule", source)
        add_boss_ai_public_input_graph(source_info, rule_id, source=source, nodes=nodes, edges=edges)
    for event in dict_items(data.get("events"))[:80]:
        event_type = str(event.get("event_type", ""))
        if event_type == "score_rule":
            event = decision_score_event(event)
            event_type = "score_delta"
        if event_type == "score_delta":
            add_boss_ai_score_graph(event, trace_id=trace_id, source=source, nodes=nodes, edges=edges)
        elif event_type == "candidate":
            candidate = candidate_from_decision_event(event)
            candidate_id = f"{source}:boss_ai_candidate:{boss_ai_candidate_key(candidate)}"
            add_graph_node(nodes, candidate_id, boss_ai_candidate_label(candidate), "boss_ai_candidate", source)
            add_graph_edge(edges, trace_id, candidate_id, "evaluates_candidate", source)
        elif event_type == "policy_check":
            attrs = event.get("attributes") if isinstance(event.get("attributes"), dict) else event
            policy_id = f"{source}:boss_ai_policy_check:{attrs.get('verdict', '')}:{attrs.get('severity', '')}"
            add_graph_node(nodes, policy_id, f"Policy {attrs.get('verdict', '')}", "boss_ai_policy_check", source)
            add_graph_edge(edges, trace_id, policy_id, "checks_policy", source)
    for event in dict_items(data.get("predicate_branch_entries"))[:60]:
        source_info = source_info_from_event(event)
        rule_id = boss_ai_rule_id(source_info, event)
        branch_id = f"{source}:boss_ai_branch:{event.get('predicate_id', '')}:{event.get('outcome', '')}:{event.get('index', '')}"
        add_graph_node(nodes, branch_id, f"{event.get('predicate_id', 'predicate')} -> {event.get('outcome', '')}", "boss_ai_predicate_branch", source)
        add_graph_edge(edges, trace_id, branch_id, "observed_predicate_branch", source)
        if rule_id:
            add_graph_node(nodes, rule_id, rule_id, "boss_ai_policy_rule", source)
            add_graph_edge(edges, rule_id, branch_id, "controls_branch", source)
            add_boss_ai_public_input_graph(source_info, rule_id, source=source, nodes=nodes, edges=edges)
        for symbol in string_items(source_info.get("dynamic_branch_legal_inputs")):
            add_graph_node(nodes, symbol, symbol, "boss_ai_public_input", source)
            add_graph_edge(edges, symbol, branch_id, "feeds_branch", source)
    for event in dict_items(data.get("public_read_probe_entries"))[:60]:
        source_info = source_info_from_event(event)
        rule_id = boss_ai_rule_id(source_info, event)
        probe_id = f"{source}:boss_ai_public_probe:{event.get('probe_id', '')}:{event.get('outcome', '')}:{event.get('index', '')}"
        add_graph_node(nodes, probe_id, f"{event.get('probe_id', 'probe')} -> {event.get('outcome', '')}", "boss_ai_public_read_probe", source)
        add_graph_edge(edges, trace_id, probe_id, "observed_public_read_probe", source)
        if rule_id:
            add_graph_node(nodes, rule_id, rule_id, "boss_ai_policy_rule", source)
            add_graph_edge(edges, rule_id, probe_id, "samples_public_input", source)
            add_boss_ai_public_input_graph(source_info, rule_id, source=source, nodes=nodes, edges=edges)
        for symbol in string_items(source_info.get("dynamic_probe_legal_inputs")):
            add_graph_node(nodes, symbol, symbol, "boss_ai_public_input", source)
            add_graph_edge(edges, symbol, probe_id, "feeds_probe", source)


def add_boss_ai_score_graph(
    event: dict[str, Any],
    *,
    trace_id: str,
    source: str,
    nodes: dict[str, dict[str, Any]],
    edges: dict[tuple[str, str, str], dict[str, Any]],
) -> None:
    source_info = source_info_from_event(event)
    rule_id = boss_ai_rule_id(source_info, event)
    candidate = event.get("candidate") if isinstance(event.get("candidate"), dict) else {}
    score_id = f"{source}:boss_ai_score_delta:{event.get('index', '')}:{rule_id}:{boss_ai_candidate_key(candidate)}"
    add_graph_node(nodes, score_id, boss_ai_score_title(event), "boss_ai_score_delta", source)
    add_graph_edge(edges, trace_id, score_id, "observed_score_delta", source)
    if rule_id:
        add_graph_node(nodes, rule_id, rule_id, "boss_ai_policy_rule", source)
        add_graph_edge(edges, rule_id, score_id, "contributes_score_delta", source)
        add_boss_ai_public_input_graph(source_info, rule_id, source=source, nodes=nodes, edges=edges)
    if candidate:
        candidate_id = f"{source}:boss_ai_candidate:{boss_ai_candidate_key(candidate)}"
        add_graph_node(nodes, candidate_id, boss_ai_candidate_label(candidate), "boss_ai_candidate", source)
        add_graph_edge(edges, candidate_id, score_id, "receives_score_delta", source)
        add_graph_edge(edges, score_id, candidate_id, "changes_candidate_score", source)


def add_boss_ai_public_input_graph(
    source_info: dict[str, Any],
    rule_id: str,
    *,
    source: str,
    nodes: dict[str, dict[str, Any]],
    edges: dict[tuple[str, str, str], dict[str, Any]],
) -> None:
    for symbol in unique_list([*string_items(source_info.get("public_reads")), *string_items(source_info.get("static_public_read_hints"))]):
        add_graph_node(nodes, symbol, symbol, "boss_ai_public_input", source)
        add_graph_edge(edges, symbol, rule_id, "uses_public_input", source)


def boss_ai_visual_proof(data: dict[str, Any]) -> str:
    if str(data.get("source", "")) == "trace_rom_pyboy_hooks":
        return "runtime_observed"
    return "planned_only"


def boss_ai_trace_type(data: dict[str, Any]) -> str:
    source = str(data.get("source", ""))
    if source == "trace_rom_pyboy_hooks":
        return "boss_ai_rom_contribution_trace"
    if source == "python_scenario":
        return "boss_ai_decision_trace"
    return "boss_ai_trace"


def boss_ai_trace_title(data: dict[str, Any], *, fallback: str) -> str:
    scenario_id = str(data.get("scenario_id") or data.get("trace_id") or "")
    if scenario_id:
        return f"Boss AI {scenario_id}"
    save_state = str(data.get("save_state") or "")
    if save_state:
        return f"Boss AI ROM trace {save_state}"
    return f"Boss AI {fallback}"


def decision_score_event(event: dict[str, Any]) -> dict[str, Any]:
    attrs = event.get("attributes") if isinstance(event.get("attributes"), dict) else {}
    rule = str(attrs.get("rule_id") or attrs.get("rule") or "")
    return {
        "event_type": "score_delta",
        "operation": "python_score_rule",
        "delta": attrs.get("delta"),
        "changed": attrs.get("delta") not in {None, 0},
        "score_before": attrs.get("before"),
        "score_after": attrs.get("after"),
        "candidate": candidate_from_decision_event(event),
        "source": {
            "rule_id": rule,
            "python_rule": rule,
            "source": str(attrs.get("source", "python_decision_trace")),
            "note": str(attrs.get("note", "")),
        },
    }


def candidate_from_decision_event(event: dict[str, Any]) -> dict[str, Any]:
    attrs = event.get("attributes") if isinstance(event.get("attributes"), dict) else event
    slot = attrs.get("slot", "")
    return {
        "kind": "move",
        "slot": slot,
        "slot_index": int(slot) - 1 if str(slot).isdigit() else attrs.get("slot_index", ""),
        "action_id": str(attrs.get("candidate_id", "")),
        "move_name": str(attrs.get("candidate_name") or attrs.get("candidate_id") or ""),
    }


def source_info_from_event(event: dict[str, Any]) -> dict[str, Any]:
    source_info = event.get("source")
    return source_info if isinstance(source_info, dict) else {}


def boss_ai_rule_id(source_info: dict[str, Any], event: dict[str, Any]) -> str:
    return str(
        event.get("rule_id")
        or source_info.get("rule_id")
        or source_info.get("python_rule")
        or source_info.get("full_symbol")
        or ""
    )


def boss_ai_event_symbols(event: dict[str, Any]) -> list[str]:
    source_info = source_info_from_event(event)
    return unique_list(
        [
            boss_ai_rule_id(source_info, event),
            str(source_info.get("source_label", "")),
            str(source_info.get("full_symbol", "")),
            *string_items(source_info.get("public_reads")),
            *string_items(source_info.get("dynamic_branch_legal_inputs")),
            *string_items(source_info.get("dynamic_probe_legal_inputs")),
        ]
    )


def boss_ai_score_title(event: dict[str, Any]) -> str:
    rule = boss_ai_rule_id(source_info_from_event(event), event) or str(event.get("operation") or "score_delta")
    return f"{rule} {event.get('score_before', '')}->{event.get('score_after', '')}"


def boss_ai_score_detail(event: dict[str, Any], *, proof: str) -> str:
    return (
        f"delta={event.get('delta', '')} changed={event.get('changed', '')} "
        f"candidate={boss_ai_candidate_label(event.get('candidate') if isinstance(event.get('candidate'), dict) else {})} "
        f"proof={proof}"
    ).strip()


def boss_ai_candidate_key(candidate: dict[str, Any]) -> str:
    return ":".join(
        part
        for part in [
            str(candidate.get("kind", "")),
            str(candidate.get("action_id") or candidate.get("move_id") or candidate.get("move_name") or ""),
            str(candidate.get("slot") or candidate.get("slot_index") or candidate.get("score_pointer") or ""),
        ]
        if part
    ) or "candidate"


def boss_ai_candidate_label(candidate: dict[str, Any]) -> str:
    name = str(candidate.get("move_name") or candidate.get("action_id") or candidate.get("move_id") or "candidate")
    slot = str(candidate.get("slot") or candidate.get("slot_index") or "")
    return f"{name} slot {slot}" if slot else name


def int_value(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def first_string(data: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str):
            return value
    return ""


def first_present(data: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in data and data.get(key) is not None:
            return data.get(key)
    return ""


def dict_items_from_mapping(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {
        str(key): str(item)
        for key, item in value.items()
        if key is not None and item is not None
    }


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


def register_provenance_for_operand(operand: dict[str, Any], attribution: dict[str, Any]) -> dict[str, Any]:
    register = str(operand.get("via_register", ""))
    operand_seq = str(operand.get("via_register_write_seq", ""))
    for provenance in dict_items(attribution.get("register_provenance")):
        if str(provenance.get("register", "")) == register and str(provenance.get("seq", "")) == operand_seq:
            return provenance
    return {
        "register": register,
        "source": str(attribution.get("source", "")),
        "seq": operand.get("via_register_write_seq"),
        "pc": str(operand.get("via_register_write_pc", "")),
        "operation": "",
        "proof_status": normalize_proof_status(attribution.get("proof_status")) or "planned_only",
    }


def dynamic_taint_edge_proof_status(proof_status: Any, *, has_taint: bool) -> str:
    proof = normalize_proof_status(proof_status) or "planned_only"
    if has_taint and proof in {"runtime_observed", "instruction_observed", "taint_proven"}:
        return "taint_proven"
    return proof


def register_provenance_id(provenance: dict[str, Any]) -> str:
    return "register_provenance:" + safe_id(
        ":".join(
            [
                str(provenance.get("register", "register")),
                str(provenance.get("source", "")),
                str(provenance.get("seq", "")),
                str(provenance.get("pc", "")),
            ]
        )
    )


def register_provenance_title(provenance: dict[str, Any]) -> str:
    register = str(provenance.get("register", "register"))
    operation = str(provenance.get("operation", "register write"))
    pc = str(provenance.get("pc_label") or provenance.get("pc") or "")
    return f"{register} <= {operation} at {pc}" if pc else f"{register} <= {operation}"


def register_provenance_detail(provenance: dict[str, Any]) -> str:
    parts = [
        f"seq={provenance.get('seq')}" if provenance.get("seq") is not None else "",
        f"value=0x{provenance.get('value_hex')}" if provenance.get("value_hex") else "",
        f"value_source={provenance.get('value_source')}" if provenance.get("value_source") else "",
        "taint=" + ",".join(string_items(provenance.get("taint"))) if string_items(provenance.get("taint")) else "",
    ]
    return " ".join(part for part in parts if part)


def add_related_evidence_graph(
    nodes: dict[str, dict[str, Any]],
    edges: dict[tuple[str, str, str], dict[str, Any]],
    target_id: str,
    item: dict[str, Any],
    *,
    source: str,
) -> None:
    if not target_id:
        return
    for symbol in string_items(item.get("related_symbols")):
        symbol = symbol_if_not_address(symbol)
        if not symbol:
            continue
        add_graph_node(nodes, symbol, symbol, "related_symbol", source)
        add_graph_edge(edges, symbol, target_id, "relates", source)
    for path in string_items(item.get("related_files")):
        add_graph_node(nodes, path, path, "related_file", source)
        add_graph_edge(edges, path, target_id, "relates", source)
    for address in related_addresses(item):
        add_graph_node(nodes, address, address, "related_address", source)
        add_graph_edge(edges, address, target_id, "addresses", source)


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


def related_addresses(item: dict[str, Any]) -> list[str]:
    addresses: list[str] = []
    addresses.extend(string_items(item.get("related_addresses")))
    addresses.extend(string_items(item.get("bank_address")))
    addresses.extend(string_items(item.get("address")))
    return unique_list(addresses)


def symbol_if_not_address(value: str) -> str:
    text = str(value)
    return "" if looks_like_address(text) else text


def looks_like_address(value: str) -> bool:
    text = str(value).strip()
    if "=" in text:
        text = text.rsplit("=", 1)[1].strip()
    if text.startswith("$"):
        text = text[1:]
    if ":" in text:
        bank, address = text.split(":", 1)
        return is_hex(bank, 2) and is_hex(address.lstrip("$"), 4)
    return is_hex(text, 4)


def is_hex(value: str, max_length: int) -> bool:
    text = str(value).strip()
    if not text or len(text) > max_length:
        return False
    return all(char in "0123456789abcdefABCDEF" for char in text)


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


def event_detail(item: dict[str, Any]) -> str:
    parts = [str(item.get("detail", ""))]
    addresses = string_items(item.get("addresses"))
    if addresses:
        parts.append("addresses=" + ", ".join(addresses))
    return " ".join(part for part in parts if part)


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
