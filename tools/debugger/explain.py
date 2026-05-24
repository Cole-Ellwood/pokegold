from __future__ import annotations

from pathlib import Path
from typing import Any

from .catalog import ROOT
from .coverage import load_traces
from .localize import normalize_path
from .reporting import load_reports
from .slicing import build_slice_report
from .workflow import command_is_runnable


SYMPTOM_SYMBOLS = {
    "damage": "wCurDamage",
    "hp": "wCurDamage",
    "boss": "BossAI_SelectMove",
    "ai": "BossAI_SelectMove",
    "score": "wEnemyAIMoveScores",
    "switch": "BossAI_SwitchOrTryItem",
    "bank": "hROMBank",
    "farcall": "hROMBank",
}
SOURCE_EXTENSIONS = {".asm", ".inc", ".py", ".md", ".txt"}


def build_explanation_report(
    *,
    reports: tuple[str, ...] = (),
    traces: tuple[str, ...] = (),
    symbols: tuple[str, ...] = (),
    watch_symbols: tuple[str, ...] = (),
    changed_files: tuple[str, ...] = (),
    symptom: str = "",
    symbols_path: str = "pokegold.sym",
    depth: int = 2,
    max_paths: int = 20,
    root: Path = ROOT,
) -> dict[str, Any]:
    loaded_reports, report_errors = load_reports(reports=reports, root=root)
    loaded_traces, trace_errors = load_traces(traces=traces, root=root)
    evidence = collect_evidence(
        loaded_reports=loaded_reports,
        loaded_traces=loaded_traces,
        symbols=symbols,
        watch_symbols=watch_symbols,
        changed_files=changed_files,
        symptom=symptom,
    )
    target_symbols = select_symbols(evidence, max_count=max_paths)
    target_files = select_files(evidence, max_count=max_paths)
    slice_report = build_slice_report(
        symbols_path=symbols_path,
        symbols=tuple(target_symbols),
        source_files=tuple(target_files),
        max_depth=max(1, depth),
        max_edges=max(20, max_paths * 4),
        root=root,
    ) if target_symbols or target_files else None
    paths = build_causal_paths(
        evidence=evidence,
        slice_report=slice_report,
        symptom=symptom,
        max_paths=max_paths,
    )
    errors = unique_list(
        [
            *report_errors,
            *trace_errors,
            *(slice_report.get("errors", []) if slice_report else []),
        ]
    )
    warnings = unique_list(
        [
            *(slice_report.get("warnings", []) if slice_report else []),
            *([] if paths else ["no causal paths were produced from the supplied evidence"]),
        ]
    )
    commands = unique_list(
        command
        for path in paths
        for command in path.get("commands", [])
    )
    return {
        "schema_version": 1,
        "kind": "unified_debugger_causal_explanation",
        "root": str(root),
        "valid": not errors,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "symbols_path": symbols_path,
        "input_reports": [item["source"] for item in loaded_reports],
        "input_traces": [item["source"] for item in loaded_traces],
        "symptom": symptom,
        "dynamic_event_count": len(evidence["events"]),
        "trace_observation_count": len(evidence["trace_observations"]),
        "content_scenario_count": len(evidence["content_scenarios"]),
        "target_symbol_count": len(target_symbols),
        "target_file_count": len(target_files),
        "target_symbols": target_symbols,
        "target_files": target_files,
        "path_count": len(paths),
        "paths": paths,
        "commands": commands[:32],
        "runnable_commands": [command for command in commands if command_is_runnable(command)][:32],
        "blocked_commands": [command for command in commands if not command_is_runnable(command)][:32],
        "slice": slice_report,
        "mermaid": render_mermaid(paths),
        "known_limits": [
            "Dynamic watch events prove that a value changed while the reported PC context was active; static edges identify plausible code/data contributors.",
            "Instruction-level dynamic taint is available through dynamic-taint when the input includes a dense opcode/register trace; otherwise paths remain bounded by the supplied evidence.",
        ],
    }


def collect_evidence(
    *,
    loaded_reports: list[dict[str, Any]],
    loaded_traces: list[dict[str, Any]],
    symbols: tuple[str, ...],
    watch_symbols: tuple[str, ...],
    changed_files: tuple[str, ...],
    symptom: str,
) -> dict[str, Any]:
    evidence = {
        "events": [],
        "trace_observations": [],
        "content_scenarios": [],
        "next_steps": [],
        "symbols": [],
        "files": [],
        "notes": [],
    }
    for symbol in symbols:
        add_symbol(evidence, symbol, source="input", weight=80)
    for symbol in watch_symbols:
        add_symbol(evidence, symbol, source="input", weight=95)
    for path in changed_files:
        add_file(evidence, path, source="input", weight=80)
    if symptom:
        evidence["notes"].append({"type": "symptom", "text": symptom, "source": "input", "weight": 50})
        for keyword, symbol in SYMPTOM_SYMBOLS.items():
            if keyword in symptom.lower():
                add_symbol(evidence, symbol, source="symptom", weight=60)
    for loaded in loaded_reports:
        collect_from_data(loaded["data"], source=loaded["source"], evidence=evidence, base_weight=70)
    for loaded in loaded_traces:
        collect_from_data(loaded["data"], source=loaded["source"], evidence=evidence, base_weight=55)
    evidence["symbols"] = merge_named_items(evidence["symbols"], "symbol")
    evidence["files"] = merge_named_items(evidence["files"], "file")
    evidence["next_steps"] = merge_next_steps(evidence["next_steps"])
    evidence["trace_observations"] = merge_trace_observations(evidence["trace_observations"])
    evidence["events"] = merge_events(evidence["events"])
    return evidence


def collect_from_data(data: Any, *, source: str, evidence: dict[str, Any], base_weight: int) -> None:
    if isinstance(data, dict):
        kind = str(data.get("kind", ""))
        for next_step in next_step_reports(data):
            collect_next_step_report(next_step, source=source, evidence=evidence, base_weight=max(base_weight, 84))
        if kind == "unified_debugger_watch_report":
            collect_watch_report(data, source=source, evidence=evidence, base_weight=max(base_weight, 90))
        elif kind == "unified_debugger_replay_plan":
            watch_report = data.get("watch_report")
            if isinstance(watch_report, dict):
                collect_watch_report(watch_report, source=source, evidence=evidence, base_weight=max(base_weight, 90))
            collect_replay_targets(data, source=source, evidence=evidence, base_weight=base_weight)
        elif kind == "unified_debugger_causal_explanation":
            for path in dict_items(data.get("paths")):
                for node in dict_items(path.get("nodes")):
                    if node.get("symbol"):
                        add_symbol(evidence, str(node["symbol"]), source=source, weight=base_weight)
                    if node.get("file"):
                        add_file(evidence, str(node["file"]), source=source, weight=base_weight)
        elif kind == "unified_debugger_trace_index":
            collect_trace_index_report(data, source=source, evidence=evidence, base_weight=max(base_weight, 82))
        elif kind == "unified_debugger_content_scenarios":
            collect_content_scenarios(data, source=source, evidence=evidence, base_weight=max(base_weight, 76))

        collect_generic_observations(data, source=source, evidence=evidence, base_weight=base_weight)
        for value in data.values():
            collect_from_data(value, source=source, evidence=evidence, base_weight=max(25, base_weight - 6))
    elif isinstance(data, list):
        for item in data:
            collect_from_data(item, source=source, evidence=evidence, base_weight=base_weight)


def next_step_reports(data: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if data.get("kind") == "unified_debugger_next_step":
        out.append(data)
    embedded = data.get("symptom_only_next_step")
    if isinstance(embedded, dict) and embedded.get("kind") == "unified_debugger_next_step":
        out.append(embedded)
    return out


def collect_next_step_report(data: dict[str, Any], *, source: str, evidence: dict[str, Any], base_weight: int) -> None:
    for candidate in next_step_candidates(data):
        source_refs = string_items(candidate.get("source_refs"))
        for source_ref in source_refs:
            if looks_like_source_path(source_ref):
                add_file(evidence, source_ref, source=source, weight=base_weight)
        evidence["next_steps"].append(
            {
                "source": source,
                "symptom": str(data.get("symptom", "")),
                "matched_lane": str(candidate.get("matched_lane") or data.get("matched_lane") or ""),
                "symptom_class": str(candidate.get("symptom_class", "")),
                "title": str(candidate.get("title") or candidate.get("symptom_class") or "next proof path"),
                "first_command": str(candidate.get("first_command") or ""),
                "required_inputs": string_items(candidate.get("required_inputs")),
                "source_refs": source_refs,
                "evidence_standard": string_items(candidate.get("evidence_standard")),
                "disproof_standard": string_items(candidate.get("disproof_standard")),
                "proof_limit": str(candidate.get("proof_limit") or ""),
                "regression_gate": str(candidate.get("regression_gate") or ""),
                "escalation_command": str(candidate.get("escalation_command") or ""),
                "repro_recipes": string_items(candidate.get("repro_recipes")),
                "weight": base_weight,
            }
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


def collect_watch_report(data: dict[str, Any], *, source: str, evidence: dict[str, Any], base_weight: int) -> None:
    for event in dict_items(data.get("events")):
        watch = str(event.get("watch", ""))
        pc_label = str(event.get("pc_label", ""))
        if watch:
            add_symbol(evidence, watch, source=source, weight=base_weight)
        if pc_label and not pc_label.startswith("$"):
            add_symbol(evidence, base_label(pc_label), source=source, weight=max(55, base_weight - 5))
        evidence["events"].append(
            {
                "type": "watch_event",
                "source": source,
                "frame": event.get("frame"),
                "watch": watch,
                "pc_label": pc_label,
                "pc_symbol": base_label(pc_label),
                "pc_bank_address": str(event.get("pc_bank_address", "")),
                "old_hex": str(event.get("old_hex", "")),
                "new_hex": str(event.get("new_hex", "")),
                "weight": base_weight,
            }
        )


def collect_replay_targets(data: dict[str, Any], *, source: str, evidence: dict[str, Any], base_weight: int) -> None:
    targets = data.get("replay_targets")
    if not isinstance(targets, dict):
        return
    for symbol in string_items(targets.get("watch_symbols")):
        add_symbol(evidence, symbol, source=source, weight=base_weight)
    for symbol in string_items(targets.get("symbols")):
        add_symbol(evidence, symbol, source=source, weight=max(35, base_weight - 10))
    for path in string_items(targets.get("source_files")):
        add_file(evidence, path, source=source, weight=max(35, base_weight - 10))


def collect_trace_index_report(data: dict[str, Any], *, source: str, evidence: dict[str, Any], base_weight: int) -> None:
    for event in dict_items(data.get("events")):
        state_symbol = str(event.get("state_symbol", ""))
        source_symbol = str(event.get("source_symbol", "") or event.get("pc_symbol", ""))
        source_file = str(event.get("source_file", ""))
        if state_symbol:
            add_symbol(evidence, state_symbol, source=source, weight=base_weight)
        if source_symbol:
            add_symbol(evidence, source_symbol, source=source, weight=max(50, base_weight - 5))
        if source_file:
            add_file(evidence, source_file, source=source, weight=max(50, base_weight - 5))
        if event.get("event_type") in {"watch_change", "score_delta", "memory_write", "memory_patch"}:
            evidence["events"].append(
                {
                    "type": "trace_index_event",
                    "source": source,
                    "frame": event.get("frame"),
                    "watch": state_symbol or str(event.get("bank_address") or event.get("address", "")),
                    "pc_label": source_symbol,
                    "pc_symbol": base_label(source_symbol),
                    "pc_bank_address": str(event.get("pc_bank_address") or event.get("bank_address", "")),
                    "old_hex": str(event.get("before", "")),
                    "new_hex": str(event.get("after", "")),
                    "weight": base_weight,
                }
            )
        evidence["trace_observations"].append(
            {
                "source": source,
                "symbol": base_label(state_symbol or source_symbol),
                "source_file": normalize_path(source_file) if source_file else "",
                "rule_id": str(event.get("rule_id", "")),
                "weight": base_weight,
            }
        )
    for causal_path in dict_items(data.get("causal_paths")):
        for node_item in dict_items(causal_path.get("nodes")):
            if node_item.get("symbol"):
                add_symbol(evidence, str(node_item["symbol"]), source=source, weight=max(45, base_weight - 10))
            if node_item.get("file"):
                add_file(evidence, str(node_item["file"]), source=source, weight=max(45, base_weight - 10))


def collect_content_scenarios(data: dict[str, Any], *, source: str, evidence: dict[str, Any], base_weight: int) -> None:
    for scenario in dict_items(data.get("scenarios")):
        scenario_id = str(scenario.get("id") or scenario.get("scenario_id") or "")
        source_file = normalize_path(str(scenario.get("source_file", "")))
        runtime_targets = scenario.get("runtime_targets") if isinstance(scenario.get("runtime_targets"), dict) else {}
        source_symbols = runtime_symbol_items(runtime_targets.get("source_symbols"))
        script_symbols = runtime_symbol_items(runtime_targets.get("script_symbols"))
        trace_symbols = runtime_symbol_items(runtime_targets.get("trace_symbols"))
        watch_symbols = runtime_symbol_items(runtime_targets.get("watch_symbols"))
        related_symbols = unique_list(
            [
                *source_symbols,
                *script_symbols,
                *trace_symbols,
                *watch_symbols,
                *runtime_symbol_items(scenario.get("related_symbols")),
            ]
        )
        if source_file:
            add_file(evidence, source_file, source=source, weight=base_weight)
        for symbol in related_symbols:
            weight = base_weight
            if symbol in watch_symbols:
                weight = max(weight, base_weight + 10)
            elif symbol in trace_symbols:
                weight = max(weight, base_weight + 6)
            add_symbol(evidence, symbol, source=source, weight=weight)
        evidence["content_scenarios"].append(
            {
                "id": scenario_id,
                "scenario_type": str(scenario.get("scenario_type", "")),
                "source": source,
                "source_file": source_file,
                "line": scenario.get("line"),
                "trigger": scenario.get("trigger") if isinstance(scenario.get("trigger"), dict) else {},
                "expected": string_items(scenario.get("expected")),
                "source_symbols": source_symbols,
                "script_symbols": script_symbols,
                "trace_symbols": trace_symbols,
                "watch_symbols": watch_symbols,
                "related_symbols": related_symbols,
                "runtime_route": str(runtime_targets.get("runtime_route", "")),
                "weight": base_weight,
            }
        )


def collect_generic_observations(data: dict[str, Any], *, source: str, evidence: dict[str, Any], base_weight: int) -> None:
    symbol = first_string(data, ("full_symbol", "symbol", "resolved", "query", "pc_label", "watch"))
    source_file = first_string(data, ("source_file",))
    rule_id = first_string(data, ("rule_id",))
    if symbol and looks_like_symbol(symbol):
        add_symbol(evidence, base_label(symbol), source=source, weight=base_weight)
    if source_file and looks_like_source_path(source_file):
        add_file(evidence, source_file, source=source, weight=base_weight)
    if symbol or source_file or rule_id:
        evidence["trace_observations"].append(
            {
                "source": source,
                "symbol": base_label(symbol),
                "source_file": normalize_path(source_file) if source_file else "",
                "rule_id": rule_id,
                "weight": base_weight,
            }
        )


def build_causal_paths(
    *,
    evidence: dict[str, Any],
    slice_report: dict[str, Any] | None,
    symptom: str,
    max_paths: int,
) -> list[dict[str, Any]]:
    slice_by_query = slice_targets_by_query(slice_report)
    paths: list[dict[str, Any]] = []
    for index, event in enumerate(evidence["events"], 1):
        path = path_from_event(index, event, slice_by_query=slice_by_query, symptom=symptom)
        paths.append(path)
    next_start = len(paths) + 1
    for offset, next_step in enumerate(evidence["next_steps"][:max_paths], next_start):
        path = path_from_next_step(offset, next_step, symptom=symptom)
        if path:
            paths.append(path)
    content_start = len(paths) + 1
    for offset, scenario in enumerate(evidence["content_scenarios"][:max_paths], content_start):
        path = path_from_content_scenario(offset, scenario, slice_by_query=slice_by_query, symptom=symptom)
        if path:
            paths.append(path)
    trace_start = len(paths) + 1
    for offset, observation in enumerate(evidence["trace_observations"][:max_paths], trace_start):
        path = path_from_trace_observation(offset, observation, slice_by_query=slice_by_query, symptom=symptom)
        if path:
            paths.append(path)
    if not paths:
        for offset, symbol in enumerate(evidence["symbols"][:max_paths], 1):
            path = path_from_static_symbol(offset, symbol, slice_by_query=slice_by_query, symptom=symptom)
            if path:
                paths.append(path)
    paths.sort(key=lambda item: (-int(item["score"]), -float(item["confidence"]), item["id"]))
    return paths[:max_paths]


def path_from_next_step(
    index: int,
    next_step: dict[str, Any],
    *,
    symptom: str,
) -> dict[str, Any] | None:
    title = str(next_step.get("title") or next_step.get("symptom_class") or "")
    first_command = str(next_step.get("first_command") or "")
    if not title and not first_command:
        return None
    source_refs = [path for path in string_items(next_step.get("source_refs")) if looks_like_source_path(path)]
    nodes = []
    symptom_text = symptom or str(next_step.get("symptom", ""))
    if symptom_text:
        nodes.append(node("symptom", "symptom", symptom_text))
    nodes.append(
        node(
            "workflow",
            "next_step",
            title or first_command,
            detail=" ".join(
                part
                for part in (
                    f"lane={next_step.get('matched_lane', '')}",
                    f"class={next_step.get('symptom_class', '')}",
                )
                if part and not part.endswith("=")
            ),
        )
    )
    if first_command:
        nodes.append(node("proof", "first_command", first_command, detail="routed first proof command"))
    for source_ref in source_refs[:5]:
        nodes.append(node("source", "source_ref", source_ref, file=source_ref))
    for standard in string_items(next_step.get("evidence_standard"))[:3]:
        nodes.append(node("proof", "evidence_standard", standard))
    for standard in string_items(next_step.get("disproof_standard"))[:3]:
        nodes.append(node("proof", "disproof_standard", standard))
    regression_gate = str(next_step.get("regression_gate") or "")
    if regression_gate:
        nodes.append(node("verify", "regression_gate", regression_gate))
    evidence = [
        f"next-step route from {next_step.get('source')}",
        "required inputs: " + "; ".join(string_items(next_step.get("required_inputs"))),
        "evidence standard: " + "; ".join(string_items(next_step.get("evidence_standard"))),
        "disproof standard: " + "; ".join(string_items(next_step.get("disproof_standard"))),
        "proof limit: " + str(next_step.get("proof_limit") or ""),
    ]
    commands = unique_list(
        [
            first_command,
            regression_gate,
            str(next_step.get("escalation_command") or ""),
            *[
                f"python -m tools.debugger repro-recipe --id {recipe}"
                for recipe in string_items(next_step.get("repro_recipes"))
            ],
        ]
    )
    return finish_path(
        path_id=f"next_step_{index}",
        title=f"Next proof path: {title or first_command}",
        score=78,
        confidence=0.64,
        nodes=nodes,
        edges=path_edges(nodes),
        evidence=evidence,
        symbols=[],
        files=unique_list(source_refs),
        extra_commands=commands,
    )


def path_from_content_scenario(
    index: int,
    scenario: dict[str, Any],
    *,
    slice_by_query: dict[str, dict[str, Any]],
    symptom: str,
) -> dict[str, Any] | None:
    scenario_id = str(scenario.get("id", ""))
    source_file = str(scenario.get("source_file", ""))
    scenario_type = str(scenario.get("scenario_type", "content_scenario"))
    if not scenario_id and not source_file:
        return None
    nodes = []
    if symptom:
        nodes.append(node("symptom", "symptom", symptom))
    nodes.append(
        node(
            "scenario",
            scenario_type or "content_scenario",
            scenario_id or scenario_type,
            file=source_file,
            line=scenario.get("line"),
            detail=trigger_detail(scenario.get("trigger", {})),
        )
    )
    if source_file:
        nodes.append(node("source", "scenario_source", source_file, file=source_file, line=scenario.get("line")))
    for symbol_name in scenario.get("source_symbols", [])[:3]:
        nodes.append(symbol_node("source", "source_label", symbol_name, slice_by_query=slice_by_query))
    for symbol_name in scenario.get("script_symbols", [])[:4]:
        nodes.append(symbol_node("source", "script_label", symbol_name, slice_by_query=slice_by_query))
    for symbol_name in scenario.get("trace_symbols", [])[:5]:
        nodes.append(symbol_node("runtime", "trace_helper", symbol_name, slice_by_query=slice_by_query))
    for symbol_name in scenario.get("watch_symbols", [])[:5]:
        nodes.append(node("state", "watch_symbol", symbol_name, symbol=symbol_name))
    related_symbols = unique_list(
        [
            *scenario.get("source_symbols", []),
            *scenario.get("script_symbols", []),
            *scenario.get("trace_symbols", []),
            *scenario.get("watch_symbols", []),
        ]
    )
    title = f"{scenario_type or 'content scenario'} {scenario_id or source_file} routes source trigger to runtime probes"
    return finish_path(
        path_id=f"content_scenario_{index}",
        title=title,
        score=74,
        confidence=0.66,
        nodes=nodes,
        edges=path_edges(nodes),
        evidence=[
            f"content scenario from {scenario.get('source')}",
            trigger_detail(scenario.get("trigger", {})),
            ", ".join(str(item) for item in scenario.get("expected", [])[:3]),
        ],
        symbols=related_symbols,
        files=unique_list([source_file]),
        extra_commands=content_scenario_commands(scenario),
    )


def path_from_event(
    index: int,
    event: dict[str, Any],
    *,
    slice_by_query: dict[str, dict[str, Any]],
    symptom: str,
) -> dict[str, Any]:
    watch = event.get("watch", "")
    pc_symbol = event.get("pc_symbol", "")
    watch_slice = slice_by_query.get(watch, {})
    pc_slice = slice_by_query.get(pc_symbol, {})
    matching_edges = [
        edge
        for edge in dict_items(watch_slice.get("incoming"))[:12]
        if edge.get("source") == pc_symbol or edge.get("source") == event.get("pc_label")
    ]
    edges = matching_edges or dict_items(watch_slice.get("incoming"))[:4]
    nodes = []
    if symptom:
        nodes.append(node("symptom", "symptom", symptom))
    nodes.append(node("state", "watch", watch, symbol=watch, detail=f"{event.get('old_hex')} -> {event.get('new_hex')}"))
    if pc_symbol:
        nodes.append(node("runtime", "pc", event.get("pc_label") or pc_symbol, symbol=pc_symbol, detail=event.get("pc_bank_address", "")))
    for edge in edges:
        nodes.append(
            node(
                "source",
                edge.get("access", "reference"),
                str(edge.get("source", "")),
                symbol=str(edge.get("source", "")),
                file=str(edge.get("path", "")),
                line=edge.get("line"),
                detail=str(edge.get("text", "")),
            )
        )
    if not edges and pc_slice.get("definition"):
        definition = pc_slice["definition"]
        nodes.append(
            node(
                "source",
                "definition",
                pc_symbol,
                symbol=pc_symbol,
                file=str(definition.get("path", "")),
                line=definition.get("line"),
            )
        )
    confidence = 0.93 if matching_edges else 0.76 if edges else 0.62
    score = 95 if matching_edges else 82 if edges else 68
    title = f"{watch} changed while {event.get('pc_label') or pc_symbol or 'unknown PC'} was executing"
    return finish_path(
        path_id=f"event_{index}",
        title=title,
        score=score,
        confidence=confidence,
        nodes=nodes,
        edges=path_edges(nodes),
        evidence=[
            f"watch event from {event.get('source')}",
            f"frame={event.get('frame')} pc={event.get('pc_bank_address')}",
            f"{watch}: {event.get('old_hex')} -> {event.get('new_hex')}",
        ],
        symbols=unique_list([watch, pc_symbol, *[str(edge.get("source", "")) for edge in edges]]),
        files=unique_list([str(edge.get("path", "")) for edge in edges if edge.get("path")]),
    )


def path_from_trace_observation(
    index: int,
    observation: dict[str, Any],
    *,
    slice_by_query: dict[str, dict[str, Any]],
    symptom: str,
) -> dict[str, Any] | None:
    symbol = observation.get("symbol", "")
    source_file = observation.get("source_file", "")
    if not symbol and not source_file:
        return None
    target_slice = slice_by_query.get(symbol, {})
    nodes = []
    if symptom:
        nodes.append(node("symptom", "symptom", symptom))
    if symbol:
        nodes.append(node("runtime", "trace_symbol", symbol, symbol=symbol, detail=observation.get("rule_id", "")))
    if source_file:
        nodes.append(node("source", "trace_source", source_file, file=source_file))
    definition = target_slice.get("definition")
    if isinstance(definition, dict) and definition.get("path"):
        nodes.append(
            node(
                "source",
                "definition",
                symbol,
                symbol=symbol,
                file=str(definition.get("path", "")),
                line=definition.get("line"),
            )
        )
    score = 64 if definition else 54
    confidence = 0.68 if definition else 0.55
    return finish_path(
        path_id=f"trace_{index}",
        title=f"Trace observed {symbol or source_file}",
        score=score,
        confidence=confidence,
        nodes=nodes,
        edges=path_edges(nodes),
        evidence=[f"trace observation from {observation.get('source')}", observation.get("rule_id", "")],
        symbols=unique_list([symbol]),
        files=unique_list([source_file, str(definition.get("path", "")) if isinstance(definition, dict) else ""]),
    )


def path_from_static_symbol(
    index: int,
    symbol: dict[str, Any],
    *,
    slice_by_query: dict[str, dict[str, Any]],
    symptom: str,
) -> dict[str, Any] | None:
    symbol_name = symbol.get("symbol", "")
    target_slice = slice_by_query.get(symbol_name, {})
    if not target_slice:
        return None
    nodes = []
    if symptom:
        nodes.append(node("symptom", "symptom", symptom))
    nodes.append(node("state", "suspect_symbol", symbol_name, symbol=symbol_name))
    definition = target_slice.get("definition") or {}
    if definition.get("path"):
        nodes.append(
            node(
                "source",
                "definition",
                symbol_name,
                symbol=symbol_name,
                file=str(definition.get("path", "")),
                line=definition.get("line"),
            )
        )
    for edge in dict_items(target_slice.get("incoming"))[:3]:
        nodes.append(
            node(
                "source",
                edge.get("access", "reference"),
                str(edge.get("source", "")),
                symbol=str(edge.get("source", "")),
                file=str(edge.get("path", "")),
                line=edge.get("line"),
                detail=str(edge.get("text", "")),
            )
        )
    return finish_path(
        path_id=f"static_{index}",
        title=f"Static causal slice for {symbol_name}",
        score=48,
        confidence=0.45,
        nodes=nodes,
        edges=path_edges(nodes),
        evidence=[f"static signal from {symbol.get('source')}"],
        symbols=unique_list([symbol_name]),
        files=unique_list([node_item.get("file", "") for node_item in nodes]),
    )


def finish_path(
    *,
    path_id: str,
    title: str,
    score: int,
    confidence: float,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    evidence: list[str],
    symbols: list[str],
    files: list[str],
    extra_commands: list[str] | None = None,
) -> dict[str, Any]:
    commands = unique_list([*(extra_commands or []), *commands_for(symbols=symbols, files=files)])
    return {
        "id": path_id,
        "title": title,
        "score": int(score),
        "confidence": round(float(confidence), 3),
        "nodes": dedupe_nodes(nodes),
        "edges": edges,
        "evidence": [item for item in evidence if item],
        "related_symbols": [item for item in symbols if item],
        "related_files": [item for item in files if item],
        "commands": commands,
    }


def commands_for(*, symbols: list[str], files: list[str]) -> list[str]:
    commands: list[str] = []
    for symbol in symbols[:4]:
        commands.append(f"python -m tools.debugger replay --symbol {symbol}")
        commands.append(f"python -m tools.debugger taint --symbol {symbol}")
        commands.append(f"python -m tools.debugger slice --symbol {symbol}")
        commands.append(f"python -m tools.debugger provenance --symbol {symbol}")
        commands.append(f"python -m tools.debugger minimize --symbol {symbol}")
    for path in files[:4]:
        commands.append(f"python -m tools.debugger slice --source-file {path}")
        commands.append(f"python -m tools.debugger gate --changed-file {path}")
    return unique_list(commands)


def content_scenario_commands(scenario: dict[str, Any]) -> list[str]:
    scenario_id = str(scenario.get("id", ""))
    source_file = str(scenario.get("source_file", ""))
    source = str(scenario.get("source", ""))
    trace_symbols = runtime_symbol_items(scenario.get("trace_symbols"))[:5]
    watch_symbols = runtime_symbol_items(scenario.get("watch_symbols"))[:5]
    script_symbols = runtime_symbol_items(scenario.get("script_symbols"))[:4]
    commands = [
        f"python -m tools.debugger setup --report {source} --scenario-id {scenario_id}",
        f"python -m tools.debugger replay --report {source} --scenario-id {scenario_id}",
        f"python -m tools.debugger coverage --report {source}",
    ]
    if source_file:
        commands.append(f"python -m tools.debugger content-mirror --source-file {source_file}")
        commands.append(f"python -m tools.debugger localize --report {source} --changed-file {source_file}")
    runtime_args = []
    for symbol in trace_symbols:
        runtime_args.extend(["--symbol", symbol])
    for symbol in watch_symbols:
        runtime_args.extend(["--watch-symbol", symbol])
    if runtime_args:
        commands.append(
            "python -m tools.debugger replay "
            + " ".join(
                [
                    "--report",
                    source,
                    "--scenario-id",
                    scenario_id,
                    *runtime_args,
                ]
            )
        )
    for symbol in unique_list([*script_symbols, *trace_symbols])[:4]:
        commands.append(f"python -m tools.debugger provenance --symbol {symbol}")
    return unique_list(commands)


def symbol_node(
    node_type: str,
    role: str,
    symbol_name: str,
    *,
    slice_by_query: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    target_slice = slice_by_query.get(symbol_name, {})
    definition = target_slice.get("definition") if isinstance(target_slice, dict) else {}
    if isinstance(definition, dict) and definition.get("path"):
        return node(
            node_type,
            role,
            symbol_name,
            symbol=symbol_name,
            file=str(definition.get("path", "")),
            line=definition.get("line"),
        )
    return node(node_type, role, symbol_name, symbol=symbol_name)


def trigger_detail(trigger: Any) -> str:
    if not isinstance(trigger, dict):
        return ""
    return ", ".join(
        f"{key}={value}"
        for key, value in trigger.items()
        if value is not None and value != ""
    )


def node(
    node_type: str,
    role: str,
    label: str,
    *,
    symbol: str = "",
    file: str = "",
    line: Any = None,
    detail: str = "",
) -> dict[str, Any]:
    return {
        "id": safe_id(f"{node_type}:{role}:{label}:{file}:{line}"),
        "type": node_type,
        "role": role,
        "label": label,
        "symbol": symbol,
        "file": normalize_path(file) if file else "",
        "line": line,
        "detail": detail,
    }


def path_edges(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    edges = []
    for left, right in zip(nodes, nodes[1:]):
        edges.append(
            {
                "from": left["id"],
                "to": right["id"],
                "relation": relation_for(left, right),
                "evidence": right.get("detail") or right.get("label", ""),
            }
        )
    return edges


def relation_for(left: dict[str, Any], right: dict[str, Any]) -> str:
    if left["type"] == "state" and right["type"] == "runtime":
        return "changed_at_pc"
    if right["role"] in {"write", "read", "call", "jump"}:
        return str(right["role"])
    if right["role"] == "definition":
        return "defined_at"
    return "supports"


def slice_targets_by_query(slice_report: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not slice_report:
        return {}
    out = {}
    for target in dict_items(slice_report.get("targets")):
        for key in (target.get("query"), target.get("resolved")):
            if key:
                out[str(key)] = target
    return out


def select_symbols(evidence: dict[str, Any], *, max_count: int) -> list[str]:
    return [
        item["symbol"]
        for item in sorted(evidence["symbols"], key=lambda item: (-int(item["weight"]), item["symbol"]))[:max_count]
        if item.get("symbol")
    ]


def select_files(evidence: dict[str, Any], *, max_count: int) -> list[str]:
    return [
        item["file"]
        for item in sorted(evidence["files"], key=lambda item: (-int(item["weight"]), item["file"]))[:max_count]
        if item.get("file")
    ]


def add_symbol(evidence: dict[str, Any], symbol: str, *, source: str, weight: int) -> None:
    name = base_label(symbol)
    if not name or not looks_like_symbol(name):
        return
    evidence["symbols"].append({"symbol": name, "source": source, "weight": int(weight)})


def add_file(evidence: dict[str, Any], path: str, *, source: str, weight: int) -> None:
    normalized = normalize_path(path)
    if not looks_like_source_path(normalized):
        return
    evidence["files"].append({"file": normalized, "source": source, "weight": int(weight)})


def merge_named_items(items: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for item in items:
        name = str(item.get(key, ""))
        if not name:
            continue
        if name not in merged:
            merged[name] = dict(item)
            merged[name]["sources"] = [str(item.get("source", ""))]
            continue
        merged[name]["weight"] = max(int(merged[name]["weight"]), int(item.get("weight", 0)))
        merged[name]["sources"] = unique_list([*merged[name]["sources"], str(item.get("source", ""))])
    return sorted(merged.values(), key=lambda item: (-int(item["weight"]), item[key]))


def merge_next_steps(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str, str], dict[str, Any]] = {}
    for item in items:
        key = (
            str(item.get("symptom_class", "")),
            str(item.get("title", "")),
            str(item.get("first_command", "")),
        )
        if key not in merged:
            merged[key] = dict(item)
            continue
        merged[key]["weight"] = max(int(merged[key].get("weight", 0)), int(item.get("weight", 0)))
        for field in ("required_inputs", "source_refs", "evidence_standard", "disproof_standard", "repro_recipes"):
            merged[key][field] = unique_list(
                [
                    *string_items(merged[key].get(field)),
                    *string_items(item.get(field)),
                ]
            )
    return sorted(merged.values(), key=lambda item: (-int(item.get("weight", 0)), item.get("title", "")))


def merge_trace_observations(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for item in items:
        key = (
            str(item.get("source", "")),
            str(item.get("symbol", "")),
            str(item.get("source_file", "")),
            str(item.get("rule_id", "")),
        )
        if key not in merged:
            merged[key] = dict(item)
    return list(merged.values())


def merge_events(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    for item in items:
        key = (
            str(item.get("source", "")),
            str(item.get("frame", "")),
            str(item.get("watch", "")),
            str(item.get("pc_label", "")),
            str(item.get("new_hex", "")),
        )
        if key not in merged:
            merged[key] = dict(item)
    return list(merged.values())


def first_string(data: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str):
            return value
    return ""


def base_label(label: str) -> str:
    text = str(label).strip()
    if not text or text.startswith("$"):
        return ""
    if "+" in text:
        text = text.split("+", 1)[0]
    return text


def looks_like_symbol(value: str) -> bool:
    text = value.strip()
    if not text or "/" in text or "\\" in text:
        return False
    if text.startswith(("$", "0x", "0X", ".", "<")):
        return False
    return text[0].isalpha() and any(char.isupper() or char == "_" for char in text)


def looks_like_source_path(value: str) -> bool:
    text = normalize_path(value)
    if not text or " " in text:
        return False
    return "/" in text and Path(text).suffix.lower() in SOURCE_EXTENSIONS


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
    if isinstance(value, dict):
        return [nested for item in value.values() for nested in string_items(item)]
    return [str(value)] if value else []


def runtime_symbol_items(value: Any) -> list[str]:
    return unique_list(
        [
            base_label(item)
            for item in string_items(value)
            if looks_like_symbol(base_label(item))
        ]
    )


def dedupe_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    seen = set()
    for item in nodes:
        if item["id"] in seen:
            continue
        seen.add(item["id"])
        out.append(item)
    return out


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
    for char in value:
        if char.isalnum():
            out.append(char)
        else:
            out.append("_")
    return "".join(out).strip("_")[:96] or "node"


def render_mermaid(paths: list[dict[str, Any]]) -> str:
    if not paths:
        return "graph TD\n"
    lines = ["graph TD"]
    emitted_nodes: set[str] = set()
    emitted_edges: set[tuple[str, str, str]] = set()
    for path in paths[:8]:
        for item in path.get("nodes", []):
            node_id = item["id"]
            if node_id in emitted_nodes:
                continue
            emitted_nodes.add(node_id)
            label = str(item.get("label", node_id)).replace('"', "'")
            lines.append(f'  {node_id}["{label}"]')
        for edge in path.get("edges", []):
            key = (edge["from"], edge["to"], edge["relation"])
            if key in emitted_edges:
                continue
            emitted_edges.add(key)
            relation = str(edge["relation"]).replace('"', "'")
            lines.append(f'  {edge["from"]} -->|{relation}| {edge["to"]}')
    return "\n".join(lines) + "\n"
